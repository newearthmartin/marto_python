import random
from django import forms
from django.db import models
from django.utils.crypto import get_random_string
from django.contrib.admin.options import ModelAdmin
from django.contrib.admin.widgets import AdminTextInputWidget
from marto_python.email import send_email
from tinymce.widgets import TinyMCE

random.seed()

# Create your models here.
class EmailMessage(models.Model):
    from_email  = models.EmailField(null=False, blank=False)
    to          = models.TextField(null=True, blank=True) #comma separated list of recipients
    cc          = models.TextField(null=True, blank=True) #comma separated list of recipients
    bcc         = models.TextField(null=True, blank=True) #comma separated list of recipients
    subject     = models.CharField(max_length=255, null=True, blank=True)
    body        = models.TextField(null=True, blank=True)
    timestamp   = models.DateTimeField(null=False, auto_now_add=True)
    def __unicode__(self):
        return self.subject
    class AdminForm(forms.ModelForm):
        class Meta:
            widgets = {
                'to': AdminTextInputWidget,
                'cc': AdminTextInputWidget,
                'bcc': AdminTextInputWidget,
                'body': TinyMCE(attrs={'cols': 120, 'rows': 50}),
            }
class EmailMessageAdmin(ModelAdmin):
    form = EmailMessage.AdminForm
    list_display = ['to', 'subject']
    list_filter = ['to', 'subject']
    search_fields = ['from_email', 'to', 'cc', 'bcc', 'subject', 'body']


#for mixing into the UserProfile model
class EmailConfirmationMixin(models.Model):
    class Meta:
        abstract = True
    email_confirmed             = models.BooleanField(blank=False, null=False, default=False, verbose_name='email confirmed')
    email_confirmation_key      = models.CharField(max_length=40, blank=True, null=True, default=None, verbose_name='email confirmation key' )

    #users should override this method if user is different from "self.user"
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
    #does not generate key
    def send_email_confirmation(self, subject, template, context=None):
        if context is None:
            context = {}
        user = self.get_user()
        context['user'] = user
        context['email_confirmation'] = self
        send_email(user.email, subject, template, context)

