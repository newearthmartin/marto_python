# encoding: utf-8
import email
import json
import datetime
import smtplib
import logging
import traceback
logger = logging.getLogger(__name__)

from django.core.mail.backends.base import BaseEmailBackend
from django.core import mail
from django.utils import timezone
from django.conf import settings

from marto_python.email.models import EmailMessage
from marto_python.util import get_full_class, load_class, setting
from marto_python.collections import list2comma_separated

class DecoratorBackend(BaseEmailBackend):
    '''abstract class for decorators to add functionality to EmailBackend in a decorator pattern'''
    inner_backend = None
    def __init__(self, inner_backend_settings_property):
        class_name = getattr(settings, inner_backend_settings_property, 'django.core.mail.backends.smtp.EmailBackend')
        logger.debug('inner backend: ' + class_name)
        if class_name:
            self.setInnerBackend( load_class(class_name)() )

    def setInnerBackend(self, backend):
        self.inner_backend = backend

    def send_messages(self, email_messages):
        if self.inner_backend:
            self.inner_backend.send_messages(email_messages)
    def open(self):
        if self.inner_backend:
            self.inner_backend.open()

    def close(self):
        if self.inner_backend:
            self.inner_backend.close()

class DBEmailBackend(DecoratorBackend):
    def __init__(self, *args, **kwargs):
        super(DBEmailBackend, self).__init__('EMAIL_DB_BACKEND_INNER_BACKEND')

    @staticmethod
    def django_message_to_db_email(message):
        connection = message.connection
        message.connection = None
        dump = json.dumps(message.__dict__)
        message.connection = connection

        email = EmailMessage()
        email.from_email    = message.from_email
        email.subject       = message.subject
        email.body          = message.body
        email.to            = list2comma_separated(message.to)
        email.cc            = list2comma_separated(message.cc)
        email.bcc           = list2comma_separated(message.bcc)
        email.email_class   = get_full_class(message)
        email.email_dump    = dump

        return email
    @staticmethod
    def db_email_to_django_message(email):
        message = load_class(email.email_class)()
        message.__dict__ = json.loads(email.email_dump)
        return message
    def send_messages(self, email_messages):
        emails = map(DBEmailBackend.django_message_to_db_email, email_messages)
        for email in emails:
            email.save()
        if getattr(settings, "EMAIL_DB_BACKEND_SEND_IMMEDIATELY", False):
            logger.info('sending emails now')
            self.send_emails(emails)
        else:
            logger.info('stored %d emails for sending later' % len(emails))
    def send_all(self):
        self.send_queryset(EmailMessage.objects)

    def send_queryset(self, emails_queryset):
        '''
        sends all emails in the queryset.
        will add the filter of sent=False
        '''
        self.send_emails(emails_queryset.filter(sent=False).all())

    def send_emails(self, emails):
        '''
        sends all db emails in list.
        '''
        MAX_TODAY = getattr(settings, 'EMAIL_DB_BACKEND_MAX_DAILY_TOTAL', 2000)
        MAX_BY_SUBJECT = getattr(settings, 'EMAIL_DB_BACKEND_MAX_DAILY_BY_SUBJECT', 700)

        yesterday24hs = timezone.now() - datetime.timedelta(days=1)
        emails_sent_today = EmailMessage.objects.filter(sent=True).filter(sent_on__gt=yesterday24hs)
        num_emails = len(emails)
        num_emails_sent_today = emails_sent_today.count()
        total_allowed_emails = MAX_TODAY - num_emails_sent_today
        logger.info('Sending emails - already sent %d emails - can send %d more' % (num_emails_sent_today, total_allowed_emails))
        if total_allowed_emails < 0:
            logger.error('Sent %d emails but only %d were allowed!' % (num_emails_sent_today, MAX_TODAY))
            return

        allowed_emails = []
        subjects = {}
        total_count = num_emails_sent_today
        for email in emails:
            if len(allowed_emails) >= total_allowed_emails:
                logger.info('reached maximum total emails')
                break
            subject = email.subject
            count = subjects[subject] if subject in subjects else emails_sent_today.filter(subject=subject).count()
            logger.debug('Already sent %d (maximum %d) for subject \'%s\'' % (count, MAX_BY_SUBJECT, subject))
            if count >= MAX_BY_SUBJECT:
                continue
            count += 1
            subjects[subject] = count
            logger.info('email with subject %s ok for sending - updated count %d - maximum %d' % (subject, count, MAX_BY_SUBJECT))
            allowed_emails.append(email)

        if allowed_emails: self.do_send(allowed_emails)

    def do_send(self, emails):
        logger.info('sending %d emails' % len(emails))
        for email in emails:
            #check again if its not sent, for concurrency
            if email.sent:
                logger.debug('email already sent %s - %s' % ((email.to, email.subject)))
                continue
            email_message = DBEmailBackend.db_email_to_django_message(email)
            email.send_succesful = False
            save = True
            try:
                super(DBEmailBackend, self).send_messages([email_message])
                email.send_succesful = True
            except (smtplib.SMTPDataError, smtplib.SMTPRecipientsRefused) as e:
                email.fail_message = unicode(e)
                logger.warn('error sending email to %s' % email.to, exc_info=True)
            except TypeError as e:
                email.fail_message = unicode(e)
                logger.warn('error sending email to %s' % email.to, exc_info=True)
            except:
                save = False
                msg = 'unknown exception sending email to %s' % email.to
                if filter(lambda name, address: address.lower() == email.to.lower(), settings.ADMINS):
                    logger.warn(msg, exc_info=True)
                else:
                    logger.error(msg, exc_info=True)
            if save:
                email.sent_on = timezone.now()
                email.sent = True
                email.save()
        logger.info('sending %d mails finished' % len(emails))

class FilteringEmailBackend(DecoratorBackend):
    filter = True
    pass_emails = []
    redirect_to = []

    def __init__(self, *args, **kwargs):
        super(FilteringEmailBackend, self).__init__('EMAIL_FILTERING_BACKEND_INNER_BACKEND')
        self.filter = setting('EMAIL_FILTERING_BACKEND_FILTER', default=True)
        self.pass_emails     = setting('EMAIL_FILTERING_BACKEND_PASS_EMAILS'    , default=[])
        self.redirect_to     = setting('EMAIL_FILTERING_BACKEND_REDIRECT_TO'    , default=[])

    def send_messages(self, email_messages):
        for message in email_messages:
            send = True
            if self.filter:
                all_recipients = message.to + message.cc + message.bcc
                for address in all_recipients:
                    if address not in self.pass_emails:
                        send = False
            status = ''
            message_string = '%s (to:%s cc:%s bcc:%s)' %  (
                                                          message.subject,
                                                          list2comma_separated(message.to),
                                                          list2comma_separated(message.cc),
                                                          list2comma_separated(message.bcc),
                                                          )
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
                    status += ' - redirecting to %s' % list2comma_separated(self.redirect_to)
                else:
                    status += ' - not redirecting'
            logger.info(status)
            if send:
                super(FilteringEmailBackend, self).send_messages(email_messages)
