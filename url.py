import logging
logger = logging.getLogger(__name__)

import urllib
import urlparse

def urlencode(string):
    enc = urllib.urlencode({'':string})
    return enc.split('=',1)[1]

def urldecode(string):
    ret = {}
    for pair in string.split('&'):
        pair = pair.split('=',1)
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
        tempVal = request.GET[param_name]
        if empty_valid or len(tempVal) > 0:
            val = tempVal
    if encode_unicode and val is not None:
        val = unicode(val)
    return val

def post_param(request, param_name, empty_valid=False, default=None, encode_unicode=True):
    val = default
    if param_name in request.POST:
        tempVal = request.POST[param_name]
        if empty_valid or len(tempVal) > 0:
            val = tempVal
    if encode_unicode and val is not None:
        val = unicode(val)
    return val

