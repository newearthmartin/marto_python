# encoding: utf-8
from django.core.validators import EmailValidator
from django.template.loader import render_to_string
from django.core.mail.message import EmailMessage
from django.contrib.sites.models import Site
from django.conf import settings
from marto_python.collections import is_list_or_tuple

email_validator = EmailValidator()

def is_email(email_str):
    try:
        email_validator(email_str)
        return True
    except:
        return False

#if sender is None, will use DEFAULT_FROM_EMAIL from settings
def send_email(to, subject, template_file, context_dict, sender=settings.DEFAULT_FROM_EMAIL):
    if not is_list_or_tuple(to):
        to = [to]
    context_dict['site'] = Site.objects.get_current()
    email_html = render_to_string(template_file, context_dict)
    email = EmailMessage(subject, email_html, sender, to)
    email.content_subtype = "html"  # Main content is now text/html
    email.send(fail_silently=False)
