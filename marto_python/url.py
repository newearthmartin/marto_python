import logging
import re
from urllib.parse import urlparse
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.validators import URLValidator, ValidationError

logger = logging.getLogger(__name__)


def is_absolute(url):
    return bool(urlparse(url).netloc)


def is_http(url):
    if not url: return False
    return re.match(r'^https?:', url, re.IGNORECASE) is not None


def request_param(request_param_dict, param_name, empty_valid=False, default=None, encode_unicode=True):
    val = default
    if param_name in request_param_dict:
        temp_val = request_param_dict[param_name]
        if empty_valid or len(temp_val) > 0:
            val = temp_val
    if encode_unicode and val is not None:
        val = str(val)
    return val


def get_server_url():
    use_https = getattr(settings, 'SERVER_USE_HTTPS', True)
    protocol = 'https' if use_https else 'http'
    return protocol + '://' + Site.objects.get_current().domain


def validate_domain(domain):
    if '://' in domain: return False
    try:
        URLValidator()(f'https://{domain}')
    except ValidationError as e:
        return False
    return True
