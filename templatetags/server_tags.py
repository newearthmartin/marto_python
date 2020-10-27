from django import template
from marto_python.url import get_server_url

register = template.Library()

@register.simple_tag
def server_url():
    return get_server_url()
