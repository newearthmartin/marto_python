import logging
from urllib.parse import urlparse
from django.conf import settings
from django.contrib.sites.models import Site

logger = logging.getLogger(__name__)


def is_absolute(url):
    return bool(urlparse(url).netloc)


def get_param(request, param_name, empty_valid=False, default=None, encode_unicode=True):
    val = default
    if param_name in request.GET:
        temp_val = request.GET[param_name]
        if empty_valid or len(temp_val) > 0:
            val = temp_val
    if encode_unicode and val is not None:
        val = str(val)
    return val


def post_param(request, param_name, empty_valid=False, default=None, encode_unicode=True):
    val = default
    if param_name in request.POST:
        temp_val = request.POST[param_name]
        if empty_valid or len(temp_val) > 0:
            val = temp_val
    if encode_unicode and val is not None:
        val = str(val)
    return val


def get_server_url():
    use_http = hasattr(settings, 'SERVER_NOT_HTTPS') and settings.SERVER_NOT_HTTPS
    protocol = 'http' if use_http else 'https'
    return protocol + '://' + Site.objects.get_current().domain
