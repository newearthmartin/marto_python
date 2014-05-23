import random
from django import forms
from django.db import models
from django.utils.crypto import get_random_string
from django.contrib.admin.options import ModelAdmin
from django.contrib.admin.widgets import AdminTextInputWidget
from marto_python.email import sendEmail
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
    emailConfirmed             = models.BooleanField(blank=False, null=False, default=False, verbose_name='email confirmed')
    emailConfirmationKey      = models.CharField(max_length=40, blank=True, null=True, default=None, verbose_name='email confirmation key' )

    #users should override this method if user is different from "self.user"
    def getUser(self):
        return self.user
    def getPrimaryEmail(self):
        return self.get_user().email

    def setEmail(self, email, addAsConfirmed=False):
        u = self.get_user()
        if email == u.email:
            return
        if addAsConfirmed:
            self.emailConfirmed = addAsConfirmed
            self.emailConfirmationKey = None
            self.save(update_fields=['emailConfirmed', 'emailConfirmationKey'])
        else:
            self.generateEmailConfirmationKey()
            
    def generateEmailConfirmationKey(self):
        self.emailConfirmationKey = get_random_string()
        self.emailConfirmed = False
        self.save(update_fields=['emailConfirmed', 'emailConfirmationKey'])
        
    def confirmEmail(self, key):
        if key == self.emailConfirmationKey:
            self.emailConfirmed = True
            self.emailConfirmationKey = None
            self.save(update_fields=['emailConfirmed', 'emailConfirmationKey'])
            return True
        else:
            return False
    #does not generate key
    def sendEmailConfirmation(self, subject, template, context=None):
        if context is None:
            context = {}
        user = self.getUser()
        context['user'] = user
        context['emailConfirmation'] = self
        sendEmail(user.email, subject, template, context)

