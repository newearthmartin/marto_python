# encoding: utf-8

from django.core.mail.backends.base import BaseEmailBackend
import email
from marto_python.email.models import EmailMessage
from marto_python.util import list2comma_separated, load_class, setting

class DecoratorBackend(BaseEmailBackend):
    '''abstract class for decorators to add functionality to EmailBackend in a decorator pattern'''      
    inner_backend = None
    def __init__(self, inner_backend_settings_property):
        class_name = setting(inner_backend_settings_property)
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
    def send_messages(self, email_messages):
        for message in email_messages:
            email = EmailMessage()
            email.sender    = message.from_email
            email.subject   = message.subject
            email.body      = message.body
            email.to        = list2comma_separated(message.to)
            email.cc        = list2comma_separated(message.cc)
            email.bcc       = list2comma_separated(message.bcc)
            #attachments: A list of attachments to put on the message. These can be either email.MIMEBase.MIMEBase instances, or (filename, content, mimetype) triples.
            #headers: A dictionary of extra headers to put on the message. The keys are the header name, values are the header values. It’s up to the caller to ensure header names and values are in the correct format for an email message. The corresponding attribute is extra_headers.
            email.save()
        super(DBEmailBackend, self).send_messages(email_messages)

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
