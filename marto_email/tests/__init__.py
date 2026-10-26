import os
from unittest import skipUnless
from smtplib import SMTPDataError, SMTPSenderRefused, SMTPServerDisconnected
import django
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail import EmailMultiAlternatives
from django.test import TestCase
from marto_email import models
from marto_email.backend import DBEmailBackend
from marto_email.testing import db_layer, mailer_settings
from marto_python.collection_utils import list2comma_separated


DIR_PATH = os.path.dirname(os.path.realpath(__file__))


class EmailTest(TestCase):
    def test_db_backend(self):
        with self.settings(**mailer_settings(['django.core.mail.backends.locmem.EmailBackend',
                                              'marto_email.backend.DBEmailBackend'])):
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


class MailersTest(TestCase):
    @skipUnless(django.VERSION >= (6, 1), 'MAILERS needs Django 6.1')
    def test_each_mailer_has_its_own_stack_and_send_immediately(self):
        FakeSMTPBackend.reset()
        transport = f'{__name__}.FakeSMTPBackend'
        with self.settings(**mailer_settings([transport, db_layer(send_immediately=True)],
                                             newsletters=[transport, db_layer(send_immediately=False)])):
            EmailMultiAlternatives('s', 'b', 'a@x.com', ['now@x.com']).send()
            self.assertEqual(['now@x.com'], FakeSMTPBackend.sent)
            self.assertEqual([True], list(models.EmailMessage.objects.values_list('sent', flat=True)))

            EmailMultiAlternatives('s', 'b', 'a@x.com', ['later@x.com']).send(using='newsletters')
            self.assertEqual(['now@x.com'], FakeSMTPBackend.sent)
            self.assertEqual(1, models.EmailMessage.objects.filter(to='later@x.com', sent=False).count())

            DBEmailBackend.instance.send_all()
            self.assertEqual(['now@x.com', 'later@x.com'], FakeSMTPBackend.sent)

    def test_send_immediately_option_beats_the_setting(self):
        FakeSMTPBackend.reset()
        with self.settings(EMAIL_DB_SEND_IMMEDIATELY=True,
                           **mailer_settings([f'{__name__}.FakeSMTPBackend', db_layer(send_immediately=False)])):
            EmailMultiAlternatives('s', 'b', 'a@x.com', ['x@x.com']).send()
        self.assertEqual([], FakeSMTPBackend.sent)
        self.assertEqual(1, models.EmailMessage.objects.filter(sent=False).count())


class FakeSMTPBackend(BaseEmailBackend):
    """Counts connections like Django's SMTP backend: send_messages opens (and then closes) one only if none is open."""
    opened = 0
    sent = []
    users = set()  # ids of the instances that sent
    errors = {}  # 1-based send attempt -> exception to raise
    disconnect_on = set()  # indexes (1-based) of send attempts that raise SMTPServerDisconnected

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connection = None

    @classmethod
    def reset(cls, disconnect_on=(), errors=None):
        cls.errors = errors or {}
        cls.opened = 0
        cls.sent = []
        cls.users = set()
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
                if type(self).attempts in self.errors:
                    raise self.errors[type(self).attempts]
                if type(self).attempts in self.disconnect_on:
                    self.connection = None
                    raise SMTPServerDisconnected('stale')
                type(self).sent.append(m.to[0])
                type(self).users.add(id(self))
        finally:
            if new_conn_created:
                self.close()
        return len(email_messages)


class DoSendConnectionTest(TestCase):
    def send_all(self, n, **kw):
        FakeSMTPBackend.reset(**kw)
        with self.settings(**mailer_settings([f'{__name__}.FakeSMTPBackend', db_layer(send_immediately=False)])):
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

    def test_row_sent_meanwhile_by_another_process_is_skipped(self):
        FakeSMTPBackend.reset()
        with self.settings(**mailer_settings([f'{__name__}.FakeSMTPBackend', db_layer(send_immediately=False)])):
            for i in range(3):
                EmailMultiAlternatives('s', 'b', 'a@x.com', [f'u{i}@x.com']).send()
            emails = list(models.EmailMessage.objects.order_by('id'))
            models.EmailMessage.objects.filter(pk=emails[1].pk).update(sent=True)  # "the other process"
            DBEmailBackend.instance.send_emails(emails)
        self.assertEqual(['u0@x.com', 'u2@x.com'], FakeSMTPBackend.sent)

    def test_each_batch_sends_through_its_own_connection(self):
        self.send_all(3)
        shared = DBEmailBackend.instance.inner_backend
        self.assertNotIn(id(shared), FakeSMTPBackend.users)  # threads share this one, so it must stay unused
        self.assertIsNone(shared.connection)

    def states(self):
        return [(e.sent, e.send_successful) for e in models.EmailMessage.objects.filter(subject='s').order_by('id')]

    def test_421_reconnects_and_retries_once(self):
        self.send_all(3, errors={2: SMTPDataError(421, b'4.4.2 timeout exceeded')})
        self.assertEqual(3, len(FakeSMTPBackend.sent))
        self.assertEqual([(True, True)] * 3, self.states())

    def test_temporary_error_leaves_email_unsent(self):
        self.send_all(3, errors={2: SMTPDataError(450, b'mailbox busy')})
        self.assertEqual(2, len(FakeSMTPBackend.sent))
        self.assertEqual([(True, True), (False, False), (True, True)], self.states())

    def test_temporary_sender_refused_leaves_email_unsent(self):
        self.send_all(3, errors={2: SMTPSenderRefused(452, b'try later', 'a@x.com')})
        self.assertEqual([(True, True), (False, False), (True, True)], self.states())

    def test_permanent_data_error_marks_email_failed(self):
        self.send_all(3, errors={2: SMTPDataError(554, b'rejected')})
        self.assertEqual([(True, True), (True, False), (True, True)], self.states())
