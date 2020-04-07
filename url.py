import logging
import urllib
import urlparse

from django.conf import settings
from django.contrib.sites.models import Site


logger = logging.getLogger(__name__)


def urlencode(string):
    enc = urllib.urlencode({'': string})
    return enc.split('=', 1)[1]


def urldecode(string):
    ret = {}
    for pair in string.split('&'):
        pair = pair.split('=', 1)
        if len(pair) == 2:
            ret[urllib.unquote_plus(pair[0])] = urllib.unquote_plus(pair[1])
        else:
            logger.error('problem urldecoding ' + pair)
    return ret



def is_absolute(url):
    return bool(urlparse.urlparse(url).netloc)


def get_param(request, param_name, empty_valid=False, default=None, encode_unicode=True):
    val = default
    if param_name in request.GET:
        temp_val = request.GET[param_name]
        if empty_valid or len(temp_val) > 0:
            val = temp_val
    if encode_unicode and val is not None:
        val = unicode(val)
    return val


def post_param(request, param_name, empty_valid=False, default=None, encode_unicode=True):
    val = default
    if param_name in request.POST:
        temp_val = request.POST[param_name]
        if empty_valid or len(temp_val) > 0:
            val = temp_val
    if encode_unicode and val is not None:
        val = unicode(val)
    return val


def get_server_url():
    protocol = 'https' if settings.DOMAIN_USE_HTTPS else 'http'
    return protocol + '://' + Site.objects.get_current().domain
