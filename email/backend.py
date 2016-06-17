# encoding: utf-8
import datetime
import logging
import smtplib
logger = logging.getLogger(__name__)

from django.core.mail.backends.base import BaseEmailBackend
from django.core import mail
from django.utils import timezone
from django.conf import settings

from marto_python.email.models import EmailMessage
from marto_python.util import list2comma_separated, load_class, setting
import email

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
        email = EmailMessage()
        email.from_email    = message.from_email
        email.subject   = message.subject
        email.body      = message.body
        email.to        = list2comma_separated(message.to)
        email.cc        = list2comma_separated(message.cc)
        email.bcc       = list2comma_separated(message.bcc)
        #attachments: A list of attachments to put on the message. These can be either email.MIMEBase.MIMEBase instances, or (filename, content, mimetype) triples.
        #headers: A dictionary of extra headers to put on the message. The keys are the header name, values are the header values. It’s up to the caller to ensure header names and values are in the correct format for an email message. The corresponding attribute is extra_headers.
        #replyto
        return email
    @staticmethod
    def db_email_to_django_message(email):
        message = mail.EmailMessage()
        message.from_email  = email.from_email
        message.subject     = email.subject
        message.body        = email.body
        message.to          = email.to.split(',')
        message.cc          = email.cc.split(',')
        message.bcc         = email.bcc.split(',')
        return message
    def send_messages(self, email_messages):
        emails = map(DBEmailBackend.django_message_to_db_email, email_messages)
        for email in emails:
            email.save()
        if getattr(settings, "EMAIL_DB_BACKEND_SEND_IMMEDIATELY", True):
            logger.info('sending emails now')
            self.do_send(emails)
        else:
            logger.info('stored emails for sending later')
    def send_all(self):
        MAX_TODAY = getattr(settings, 'EMAIL_DB_BACKEND_MAX_DAILY_TOTAL', 2000)
        MAX_BY_SUBJECT = getattr(settings, 'EMAIL_DB_BACKEND_MAX_DAILY_BY_SUBJECT', 700)

        yesterday24hs = timezone.now() - datetime.timedelta(days=1)
        emails = EmailMessage.objects.filter(sent=False)
        emails_sent_today = EmailMessage.objects.filter(sent=True).filter(sent_on__gt=yesterday24hs)
        num_emails = emails.count()
        num_emails_sent_today = emails_sent_today.count()
        total_allowed_emails = MAX_TODAY - num_emails_sent_today
        logger.info('Sending emails - already sent %d emails - can send %d more' % (num_emails_sent_today, total_allowed_emails))
        if total_allowed_emails < 0:
            logger.error('Sent %d emails but only %d were allowed!' % (num_emails_sent_today, MAX_TODAY))
            return

        allowed_emails = []
        subjects = {}
        total_count = num_emails_sent_today
        for email in emails.all():
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
            try:
                email.failed_send = True
                super(DBEmailBackend, self).send_messages([email_message])
                email.failed_send = False
            except smtplib.SMTPDataError:
                logger.error('error sending email - %s - %s' % (email.to, email.subject))
            email.sent_on = timezone.now()
            email.sent = True
            email.save()
        #email_messages = map(DBEmailBackend.db_email_to_django_message, emails)
        #super(DBEmailBackend, self).send_messages(email_messages)
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
            print status
            if send:
                super(FilteringEmailBackend, self).send_messages(email_messages)
