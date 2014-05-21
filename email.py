# encoding: utf-8

import random
from django.conf import settings
from django.db import models
from django.utils.crypto import get_random_string
from django.core.validators import email_re
from marto_python.util import isListOrTuple
from django.template.loader import render_to_string
from django.core.mail.message import EmailMultiAlternatives
from django.contrib.sites.models import Site

random.seed()

def isEmail(email_str):
    return True if email_re.match(email_str) else False

def sendEmail(to, subject, template_file, context_dict, sender=settings.DEFAULT_FROM_EMAIL):
    if not isListOrTuple(to):
        to = [to]
    context_dict['site'] = Site.objects.get_current()
    email_html = render_to_string(template_file, context_dict)
    email = EmailMultiAlternatives(subject, 'necesitas un cliente de correo html para ver este mail', sender, to)            
    email.attach_alternative(email_html, "text/html")
    email.send(fail_silently=False)

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
#testing
