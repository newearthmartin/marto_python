import os
from django.core.mail import EmailMultiAlternatives
from django.test import TestCase
from marto_python.email import models
from marto_python.email.backend import DBEmailBackend
from marto_python.collection_utils import list2comma_separated


DIR_PATH = os.path.dirname(os.path.realpath(__file__))


class EmailTest(TestCase):
    def test_db_backend(self):
        with self.settings(EMAIL_BACKEND='marto_python.email.backend.StackedEmailBackend',
                           EMAIL_BACKEND_STACK = ['django.core.mail.backends.locmem.EmailBackend',
                                                  'marto_python.email.backend.DBEmailBackend']):
            self.assertEqual(0, models.EmailMessage.objects.count())
            subject = "Test subject"
            body = "Test body"
            email1 = "test1@multilanguage.xyz"
            email2 = "test2@multilanguage.xyz"
            email3 = "test3@multilanguage.xyz"
            msg = EmailMultiAlternatives(subject=subject, body=body, from_email=email1, to=[email2, email3])
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
