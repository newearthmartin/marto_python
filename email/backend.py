import json
import datetime
import smtplib
import logging

from django.conf import settings
from django.utils import timezone
from django.core.mail.backends.base import BaseEmailBackend

from marto_python.email.models import EmailMessage
from marto_python.util import get_full_class, load_class, setting
from marto_python.collections import list2comma_separated

logger = logging.getLogger(__name__)


class DecoratorBackend(BaseEmailBackend):
    """abstract class for decorators to add functionality to EmailBackend in a decorator pattern"""
    inner_backend = None

    def __init__(self, *args, **kwargs):
        super(DecoratorBackend, self).__init__(*args, **kwargs)
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
        for backend_class in settings.EMAIL_BACKEND_STACK:
            inner_backend = load_class(backend_class)(*args, inner_backend=inner_backend, **kwargs)
        super(StackedEmailBackend, self).__init__(*args, inner_backend=inner_backend, **kwargs)


class DBEmailBackend(DecoratorBackend):
    def __init__(self, *args, **kwargs):
        super(DBEmailBackend, self).__init__(*args, **kwargs)
        if not self.inner_backend:
            class_name = setting('EMAIL_DB_INNER_BACKEND',
                                 default='django.core.mail.backends.smtp.EmailBackend')
            if class_name:
                self.set_inner_backend_class(class_name)

    @staticmethod
    def django_message_to_db_email(message):
        connection = message.connection
        message.connection = None
        dump = json.dumps(message.__dict__)
        message.connection = connection
        email = EmailMessage()
        email.from_email =  message.from_email
        email.subject =     message.subject
        email.body =        message.body
        email.to =          list2comma_separated(message.to)
        email.cc =          list2comma_separated(message.cc)
        email.bcc =         list2comma_separated(message.bcc)
        email.email_class = get_full_class(message)
        email.email_dump =  dump
        return email

    @staticmethod
    def db_email_to_django_message(email):
        message = load_class(email.email_class)()
        message.__dict__ = json.loads(email.email_dump)
        return message

    def send_messages(self, email_messages):
        db_emails = list(map(DBEmailBackend.django_message_to_db_email, email_messages))
        for email in db_emails:
            email.save()
        if setting('EMAIL_DB_SEND_IMMEDIATELY', True):
            logger.debug('sending emails now')
            self.send_emails(db_emails)
        else:
            logger.info(f'stored {len(db_emails)} emails for sending later')

    def send_all(self):
        self.send_queryset(EmailMessage.objects)

    def send_queryset(self, emails_queryset):
        """
        sends all emails in the queryset that haven't been sent
        """
        self.send_emails(emails_queryset.filter(sent=False).all())

    def send_emails(self, emails):
        """
        sends all db emails in list.
        """
        max_today = getattr(settings, 'EMAIL_DB_MAX_DAILY_TOTAL', 2000)
        max_by_subject = getattr(settings, 'EMAIL_DB_MAX_DAILY_BY_SUBJECT', 700)

        yesterday24hs = timezone.now() - datetime.timedelta(days=1)
        emails_sent_today = EmailMessage.objects.filter(sent=True).filter(sent_on__gt=yesterday24hs)
        num_emails_sent_today = emails_sent_today.count()
        total_allowed_emails = max_today - num_emails_sent_today
        logger.debug(f'Sending emails'
                     f' - already sent {num_emails_sent_today} emails'
                     f' - can send {total_allowed_emails} more')
        if total_allowed_emails < 0:
            logger.error(f'Sent {num_emails_sent_today} emails but only {max_today} were allowed!')
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
            logger.info(f'sending email - subject: {subject}')
            logger.debug(f'sending email - ok for sending - updated count {count} - maximum {max_by_subject}')
            allowed_emails.append(email)

        if allowed_emails: self.do_send(allowed_emails)

    def do_send(self, emails):
        logger.info(f'sending {len(emails)} emails')
        for email in emails:
            # check again if its not sent, for concurrency
            if email.sent:
                logger.debug(f'email already sent {email.to} - {email.subject}')
                continue
            email_message = DBEmailBackend.db_email_to_django_message(email)
            email.sent = False
            email.send_successful = False
            try:
                super(DBEmailBackend, self).send_messages([email_message])
                email.send_successful = True
                email.sent = True
            except (smtplib.SMTPDataError, smtplib.SMTPRecipientsRefused) as e:
                email.fail_message = str(e)
                logger.warning(f'error sending email to {email.to}', exc_info=True)
                email.sent = True
            except TypeError as e:
                email.fail_message = str(e)
                logger.warning(f'error sending email to {email.to}', exc_info=True)
                email.sent = True
            except smtplib.SMTPConnectError:
                logger.warning(f'error sending email to {email.to}', exc_info=True)
            except:
                msg = f'unknown exception sending email to {email.to}'
                has_admin_emails = [e for e in settings.ADMINS if e[1].lower() == email.to.lower()]
                if has_admin_emails:
                    logger.warning(msg, exc_info=True)
                else:
                    logger.error(msg, exc_info=True)
            if email.sent:
                email.sent_on = timezone.now()
                email.save()
        logger.debug(f'sending {len(emails)} emails - finished')


class FilteringEmailBackend(DecoratorBackend):
    filter = True
    pass_emails = []
    redirect_to = []

    def __init__(self, *args, **kwargs):
        class_name = setting('EMAIL_FILTERING_INNER_BACKEND',
                             default='django.core.mail.backends.smtp.EmailBackend')
        super(FilteringEmailBackend, self).__init__(*args, inner_backend_class=class_name, **kwargs)
        self.filter = setting('EMAIL_FILTERING_FILTER', default=True)
        self.pass_emails = setting('EMAIL_FILTERING_PASS_EMAILS', default=[])
        self.redirect_to = setting('EMAIL_FILTERING_REDIRECT_TO', default=[])

    def send_messages(self, email_messages):
        for message in email_messages:
            send = True
            if self.filter:
                all_recipients = message.to + message.cc + message.bcc
                for address in all_recipients:
                    if address not in self.pass_emails:
                        send = False
            message_string = f'{message.subject} (' \
                             f' to:{list2comma_separated(message.to)}' \
                             f' cc:{list2comma_separated(message.cc)}' \
                             f' bcc:{list2comma_separated(message.bcc)}' \
                             f')'
            if send:
                status = 'SENDING E-MAIL - ' + message_string
            else:
                status = 'FILTERING E-MAIL - ' + message_string
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
                super(FilteringEmailBackend, self).send_messages(email_messages)
