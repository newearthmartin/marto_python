# encoding: utf-8
from django.core.validators import email_re
from marto_python.util import isListOrTuple
from django.template.loader import render_to_string
from django.core.mail.message import EmailMessage
from django.contrib.sites.models import Site
from django.conf import settings

def isEmail(email_str):
    return True if email_re.match(email_str) else False

#if sender is None, will use DEFAULT_FROM_EMAIL from settings
def sendEmail(to, subject, template_file, context_dict, sender=settings.DEFAULT_FROM_EMAIL):
    if not isListOrTuple(to):
        to = [to]
    context_dict['site'] = Site.objects.get_current()
    email_html = render_to_string(template_file, context_dict)
    
    #no usando EmailMultiAlternatives 
    #email = EmailMultiAlternatives(subject, 'necesitas un cliente de correo html para ver este mail', sender, to)
    #email.attach_alternative(email_html, "text/html")
    #sino EmailMessage
    email = EmailMessage(subject, email_html, sender, to)
    email.content_subtype = "html"  # Main content is now text/html

    email.send(fail_silently=False)
