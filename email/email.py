from django.core.validators import EmailValidator
from django.template.loader import render_to_string
from django.core.mail.message import EmailMessage
from django.core.exceptions import ValidationError
from django.contrib.sites.models import Site
from django.conf import settings
from marto_python.collection_utils import is_list_or_tuple
from marto_python.url import get_server_url

email_validator = EmailValidator()


def is_email(email_str):
    try:
        email_validator(email_str)
        return True
    except ValidationError:
        return False


def send(to, subject, email_html, sender=settings.DEFAULT_FROM_EMAIL, cc=None, bcc=None):
    email = EmailMessage(subject, email_html, sender, to, cc=cc, bcc=bcc)
    email.content_subtype = "html"  # Main content is now text/html
    email.send(fail_silently=False)


def send_email(to, subject, template_file, context_dict, sender=settings.DEFAULT_FROM_EMAIL):
    if not is_list_or_tuple(to):
        to = [to]
    context_dict['site'] = Site.objects.get_current()
    context_dict['server_url'] = get_server_url()
    email_html = render_to_string(template_file, context_dict)
    send(to, subject, email_html, sender=sender)


def send_email_to_admins(subject, email_html):
    admin_emails = map(lambda e: e[1], settings.ADMINS)
    send(admin_emails, subject, email_html)

