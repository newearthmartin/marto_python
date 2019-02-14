import logging
from urllib.parse import urlencode, unquote_plus, urlparse

logger = logging.getLogger(__name__)

"""
# FIXME: why these methods?
def url_encode(string):
    enc = urlencode({'': string})
    return enc.split('=', 1)[1]


def url_decode(string):
    ret = {}
    for pair in string.split('&'):
        pair = pair.split('=', 1)
        if len(pair) == 2:
            ret[unquote_plus(pair[0])] = unquote_plus(pair[1])
        else:
            logger.error('problem urldecoding ' + pair)
    return ret
"""

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

