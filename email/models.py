import random
from django.db import models
from django.utils.crypto import get_random_string
from marto_python.email.email import send_email

random.seed()


class EmailMessage(models.Model):
    from_email = models.CharField(max_length=512, null=False, blank=False)
    to = models.TextField(null=True, blank=True)  # comma separated list of recipients
    cc = models.TextField(null=True, blank=True)  # comma separated list of recipients
    bcc = models.TextField(null=True, blank=True)  # comma separated list of recipients
    subject = models.CharField(max_length=512, null=True, blank=True)
    body = models.TextField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    sent = models.BooleanField(default=False, db_index=True)
    sent_on = models.DateTimeField(null=True, blank=True, db_index=True)
    send_successful = models.BooleanField(default=False)
    fail_message = models.CharField(max_length=256, null=True, blank=True)
    email_class = models.CharField(max_length=256)
    email_dump = models.TextField()

    def __unicode__(self):
        return self.subject

    def clear_sent(self):
        self.sent = False
        self.send_successful = False
        self.fail_message = None
        self.sent_on = None
        self.save()


class EmailConfirmationMixin(models.Model):
    """ For mixing into the UserProfile model """
    class Meta:
        abstract = True

    email_confirmed = models.BooleanField(blank=False, null=False, default=False,
                                          verbose_name='email confirmed')
    email_confirmation_key = models.CharField(max_length=100, blank=True, null=True, default=None,
                                              verbose_name='email confirmation key')

    # users should override this method if user is different from "self.user"
    def get_user(self):
        return self.user

    def get_primary_email(self):
        return self.get_user().email

    def set_email(self, email, add_as_confirmed=False):
        u = self.get_user()
        if email == u.email:
            return
        if add_as_confirmed:
            self.email_confirmed = add_as_confirmed
            self.email_confirmation_key = None
            self.save(update_fields=['email_confirmed', 'email_confirmation_key'])
        else:
            self.generate_confirmation_key()

    def generate_confirmation_key(self):
        self.email_confirmation_key = get_random_string()
        self.email_confirmed = False
        self.save(update_fields=['email_confirmed', 'email_confirmation_key'])

    def confirm_email(self, key):
        if key == self.email_confirmation_key:
            self.email_confirmed = True
            self.email_confirmation_key = None
            self.save(update_fields=['email_confirmed', 'email_confirmation_key'])
            return True
        else:
            return False

    def send_email_confirmation(self, subject, template, context=None):  # does not generate key
        if context is None:
            context = {}
        user = self.get_user()
        context['user'] = user
        context['email_confirmation'] = self
        send_email(user.email, subject, template, context)
