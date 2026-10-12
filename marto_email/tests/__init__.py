import os
from smtplib import SMTPServerDisconnected
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail import EmailMultiAlternatives
from django.test import TestCase
from marto_email import models
from marto_email.backend import DBEmailBackend
from marto_python.collection_utils import list2comma_separated


DIR_PATH = os.path.dirname(os.path.realpath(__file__))


class EmailTest(TestCase):
    def test_db_backend(self):
        with self.settings(EMAIL_BACKEND='marto_email.backend.StackedEmailBackend',
                           EMAIL_BACKEND_STACK = ['django.core.mail.backends.locmem.EmailBackend',
                                                  'marto_email.backend.DBEmailBackend']):
            self.assertEqual(0, models.EmailMessage.objects.count())
            subject = "Test subject"
            body = "Test body"
            email1 = "test1@multilanguage.xyz"
            email2 = "test2@multilanguage.xyz"
            email3 = "test3@multilanguage.xyz"
            msg = EmailMultiAlternatives(subject=subject, body=body, from_email=email1, to=[email2, email3])
            msg.attach_file(os.path.join(DIR_PATH, '../tests/krishna.jpg'), 'image/jpeg')
            msg.send()
            self.assertEqual(1, models.EmailMessage.objects.count())
            email_obj = models.EmailMessage.objects.first()
            self.assertEqual(email_obj.subject, subject)
            self.assertEqual(email_obj.body, body)
            self.assertEqual(email_obj.from_email, email1)
            self.assertEqual(email_obj.to, list2comma_separated([email2, email3]))

            msg2 = DBEmailBackend.db_email_to_django_message(email_obj)
            self.assertEqual(msg.subject, msg2.subject)
            self.assertEqual(msg.to, msg2.to)
            self.assertEqual(msg.body, msg2.body)
            self.assertEqual(msg.attachments, msg2.attachments)
            self.assertEqual(msg.alternatives, msg2.alternatives)


class FakeSMTPBackend(BaseEmailBackend):
    """Counts connections like Django's SMTP backend: send_messages opens (and then closes) one only if none is open."""
    opened = 0
    sent = []
    disconnect_on = set()  # indexes (1-based) of send attempts that raise SMTPServerDisconnected

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connection = None

    @classmethod
    def reset(cls, disconnect_on=()):
        cls.opened = 0
        cls.sent = []
        cls.attempts = 0
        cls.disconnect_on = set(disconnect_on)

    def open(self):
        if self.connection:
            return False
        type(self).opened += 1
        self.connection = object()
        return True

    def close(self):
        self.connection = None

    def send_messages(self, email_messages):
        new_conn_created = self.open()
        try:
            for m in email_messages:
                type(self).attempts += 1
                if type(self).attempts in self.disconnect_on:
                    self.connection = None
                    raise SMTPServerDisconnected('stale')
                type(self).sent.append(m.to[0])
        finally:
            if new_conn_created:
                self.close()
        return len(email_messages)


class DoSendConnectionTest(TestCase):
    def send_all(self, n, **kw):
        FakeSMTPBackend.reset(**kw)
        with self.settings(EMAIL_BACKEND='marto_email.backend.StackedEmailBackend',
                           EMAIL_DB_SEND_IMMEDIATELY=False,
                           EMAIL_BACKEND_STACK=[f'{__name__}.FakeSMTPBackend', 'marto_email.backend.DBEmailBackend']):
            for i in range(n):
                EmailMultiAlternatives('s', 'b', 'a@x.com', [f'u{i}@x.com']).send()
            self.assertEqual(0, len(FakeSMTPBackend.sent))
            DBEmailBackend.instance.send_all()

    def test_one_connection_for_the_batch(self):
        self.send_all(5)
        self.assertEqual(1, FakeSMTPBackend.opened)
        self.assertEqual(5, len(FakeSMTPBackend.sent))
        self.assertEqual(5, models.EmailMessage.objects.filter(sent=True).count())

    def test_stale_connection_reconnects_and_retries_once(self):
        self.send_all(5, disconnect_on=[3])
        self.assertEqual(2, FakeSMTPBackend.opened)
        self.assertEqual(5, len(FakeSMTPBackend.sent))
        self.assertEqual(5, models.EmailMessage.objects.filter(sent=True).count())

    def test_emails_are_loaded_and_sent_in_batches(self):
        with self.settings(EMAIL_DB_BATCH_SIZE=2):
            self.send_all(5)
        self.assertEqual(3, FakeSMTPBackend.opened)  # 2 + 2 + 1, one connection per batch
        self.assertEqual(5, len(FakeSMTPBackend.sent))
        self.assertEqual(5, models.EmailMessage.objects.filter(sent=True).count())
