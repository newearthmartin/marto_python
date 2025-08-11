import json
import datetime
import logging
import pickle

from smtplib import SMTPDataError, SMTPConnectError, SMTPRecipientsRefused

from django.conf import settings
from django.db.models import QuerySet, Manager
from django.utils import timezone
from django.core.mail.backends.base import BaseEmailBackend

from marto_python.email.models import EmailMessage
from marto_python.util import get_full_class, load_class, setting
from marto_python.collection_utils import list2comma_separated

logger = logging.getLogger(__name__)


class DecoratorBackend(BaseEmailBackend):
    """Abstract class for decorators to add functionality to EmailBackend in a decorator pattern"""
    inner_backend = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        backend_instance = kwargs.get('inner_backend')
        backend_class = kwargs.get('inner_backend_class')
        if backend_instance: self.set_inner_backend(backend_instance)
        elif backend_class: self.set_inner_backend_class(backend_class)

    def set_inner_backend(self, backend):
        self.inner_backend = backend

    def set_inner_backend_class(self, backend_class):
        self.set_inner_backend(load_class(backend_class)())

    def send_messages(self, email_messages):
        if self.inner_backend:
            self.inner_backend.send_messages(email_messages)

    def open(self):
        if self.inner_backend:
            self.inner_backend.open()

    def close(self):
        if self.inner_backend:
            self.inner_backend.close()


class StackedEmailBackend(DecoratorBackend):
    def __init__(self, *args, **kwargs):
        inner_backend = None
        for backend_class_name in settings.EMAIL_BACKEND_STACK:
            backend_class = load_class(backend_class_name)
            inner_backend = backend_class(*args, inner_backend=inner_backend, **kwargs)
        super().__init__(*args, inner_backend=inner_backend, **kwargs)


class DBEmailBackend(DecoratorBackend):
    instance = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        DBEmailBackend.instance = self
        if not self.inner_backend:
            class_name = setting('EMAIL_DB_INNER_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
            self.set_inner_backend_class(class_name)

    @staticmethod
    def django_message_to_db_email(message):
        email = EmailMessage()
        email.from_email = message.from_email
        email.subject = message.subject
        email.body = message.body
        email.to = list2comma_separated(message.to)
        email.cc = list2comma_separated(message.cc)
        email.bcc = list2comma_separated(message.bcc)
        email.email_class = get_full_class(message)

        msg_dict = message.__dict__.copy()
        msg_dict.pop('connection')
        binary_dict = {}
        if message.attachments:
            binary_dict['attachments'] = message.attachments
            msg_dict.pop('attachments')
        if alternatives := getattr(message, 'alternatives', None):
            binary_dict['alternatives'] = alternatives
            msg_dict.pop('alternatives')
        if binary_dict:
            email.email_dump_binary = pickle.dumps(binary_dict)
        email.email_dump = json.dumps(msg_dict)
        return email

    @staticmethod
    def db_email_to_django_message(email):
        msg_dict = json.loads(email.email_dump)
        if email.email_dump_binary:
            binary_dict = pickle.loads(email.email_dump_binary)
            if attachments := binary_dict.get('attachments', None): msg_dict['attachments'] = attachments
            if alternatives := binary_dict.get('alternatives', None): msg_dict['alternatives'] = alternatives
        message = load_class(email.email_class)()
        message.__dict__ = msg_dict
        return message

    def send_messages(self, email_messages):
        db_emails = [DBEmailBackend.django_message_to_db_email(m) for m in email_messages]
        for email in db_emails:
            email.save()
        if not setting('EMAIL_DB_SEND_IMMEDIATELY', True):
            logger.info(f'Stored {len(db_emails)} emails for sending later')
            return
        logger.debug('Sending emails now')
        self.send_emails(db_emails)

    def send_all(self):
        self.send_queryset(EmailMessage.objects)

    def send_queryset(self, emails_qs: QuerySet | Manager):
        """Sends all emails in the queryset that haven't been sent"""
        self.send_emails(emails_qs.filter(sent=False).all())

    def send_emails(self, emails):
        """Sends all db emails in list."""
        max_today = getattr(settings, 'EMAIL_DB_MAX_DAILY_TOTAL', 2000)
        max_by_subject = getattr(settings, 'EMAIL_DB_MAX_DAILY_BY_SUBJECT', 700)

        yesterday24hs = timezone.now() - datetime.timedelta(days=1)
        emails_sent_today = EmailMessage.objects.filter(sent=True).filter(sent_on__gt=yesterday24hs)
        num_emails_sent_today = emails_sent_today.count()
        total_allowed_emails = max_today - num_emails_sent_today
        logger.debug(f'Sending emails - already sent {num_emails_sent_today} - can send {total_allowed_emails} more')
        if total_allowed_emails < 0:
            logger.warning(f'Sent {num_emails_sent_today} emails but only {max_today} were allowed!')
            return

        allowed_emails = []
        subjects = {}
        for email in emails:
            if len(allowed_emails) >= total_allowed_emails:
                logger.warning('reached maximum total emails')
                break
            subject = email.subject
            count = subjects[subject] if subject in subjects else emails_sent_today.filter(subject=subject).count()
            logger.debug(f'Already sent {count} (maximum {max_by_subject}) for subject "{subject}"')
            if count >= max_by_subject:
                continue
            count += 1
            subjects[subject] = count
            logger.info(f'Sending email - subject: {subject}')
            logger.debug(f'Sending email - ok for sending - updated count {count} - maximum {max_by_subject}')
            allowed_emails.append(email)

        if allowed_emails: self.do_send(allowed_emails)

    def do_send(self, emails):
        logger.info(f'Sending {len(emails)} emails')
        for email in emails:
            # Using log_fn to prevent infinite loop when sending errors to admins
            # because logger.error creates a new email
            has_admin_emails = [e for e in settings.ADMINS if e[1].lower() == email.to.lower()]
            log_fn = logger.error if not has_admin_emails else logger.warning

            # Check again if it's not sent, for concurrency
            email.refresh_from_db()
            if email.sent:
                logger.debug(f'Email already sent {email.to} - {email.subject}')
                continue

            email_message = DBEmailBackend.db_email_to_django_message(email)
            try:
                super().send_messages([email_message])
                email.send_successful = True
            except SMTPRecipientsRefused as e:
                email.fail_message = str(e)
                logger.warning(f'Email recipients refused: {email.to}', exc_info=True)
            except SMTPDataError as e:
                email.fail_message = str(e)
                log_fn(f'SMTP data error sending email to {email.to}', exc_info=True)
            except TypeError:
                log_fn(f'Type error when sending email to {email.to}', exc_info=True)
                continue
            except (SMTPConnectError, ConnectionResetError, TimeoutError):
                logger.warning(f'Connection error when sending email to {email.to}', exc_info=True)
                continue
            except:
                msg = f'Unexpected exception sending email to {email.to}'
                log_fn(msg, exc_info=True)
                continue
            email.sent = True
            email.sent_on = timezone.now()
            email.save()
        logger.debug(f'sending {len(emails)} emails - finished')


class FilteringEmailBackend(DecoratorBackend):
    pass_emails = []
    redirect_to = []

    def __init__(self, *args, **kwargs):
        class_name = setting('EMAIL_FILTERING_INNER_BACKEND',
                             default='django.core.mail.backends.smtp.EmailBackend')
        super().__init__(*args, inner_backend_class=class_name, **kwargs)
        self.pass_emails = setting('EMAIL_FILTERING_PASS_EMAILS', default=[])
        self.redirect_to = setting('EMAIL_FILTERING_REDIRECT_TO', default=[])

    def send_messages(self, email_messages):
        for message in email_messages:
            send = True
            all_recipients = message.to + message.cc + message.bcc
            for address in all_recipients:
                if address not in self.pass_emails:
                    send = False
            message_to = list2comma_separated(message.to)
            message_cc = list2comma_separated(message.cc)
            message_bcc = list2comma_separated(message.bcc)
            message_string = f'{message.subject} (to:{message_to} cc:{message_cc} bcc:{message_bcc})'
            if send:
                status = 'filter pass - ' + message_string
            else:
                status = 'filter NOT pass - ' + message_string
                if self.redirect_to:
                    message.subject = 'REDIRECTED - ' + message_string
                    message.to = self.redirect_to
                    message.cc = []
                    message.bcc = []
                    send = True
                    status += f' - redirecting to {list2comma_separated(self.redirect_to)}'
                else:
                    status += ' - not redirecting'
            logger.info(status)
            if send:
                super().send_messages(email_messages)
