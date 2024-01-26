import json
from django.test import TestCase
from .models import BlockedAddress, EmailMessage
from .backend import DBEmailBackend
from .email import send


class EmailTest(TestCase):
    def test_blocked(self):
        email = EmailMessage('test subject', 'test content',
                             to=['test1@test.com', 'test2@test.com'],
                             cc=['test2@test.com', 'test3@test.com'],
                             bcc=['test3@test.com', 'test4@test.com'])
        originals = [email.to, email.cc, email.bcc]
        self.assertTrue(DBEmailBackend.remove_blocked_addresses(email))
        self.assertEqual([email.to, email.cc, email.bcc], originals)
        self.assertIsNone(email.blocked_addresses)

        BlockedAddress(email='test2@test.com').save()

        self.assertTrue(DBEmailBackend.remove_blocked_addresses(email))
        self.assertEqual(email.to, ['test1@test.com'])
        self.assertEqual(email.cc, ['test3@test.com'])
        self.assertEqual(email.bcc, ['test3@test.com', 'test4@test.com'])
        self.assertIsNotNone(email.blocked_addresses)

        BlockedAddress(email='test1@test.com').save()
        BlockedAddress(email='test3@test.com').save()
        BlockedAddress(email='test4@test.com').save()

        self.assertFalse(DBEmailBackend.remove_blocked_addresses(email))
        self.assertEqual(email.to, [])
        self.assertEqual(email.cc, [])
        self.assertEqual(email.bcc, [])
        self.assertEqual(set(json.loads(email.blocked_addresses)), {'test1@test.com', 'test2@test.com','test3@test.com','test4@test.com'})

        # BlockedAddress(email='blocked1@test.com').save()
        # send(['blocked1@test.com'], 'subject', 'content')
        # DBEmailBackend.instance.send_all()
