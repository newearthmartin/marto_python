# encoding: utf-8
import math
import base64
import os
import urllib
import logging
import importlib
import time,datetime
from string import atoi
from Crypto.Cipher import DES
from django.conf import settings
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


class ErrorCode:
    def __init__(self, code, message):
        self.code = code
        self.message = message
    code = 0
    message = None


def add_message(request, message):
    add_list_elem(request.session, 'messages', message)


def add_list_elem(d, key, elem):
    if d.has_key(key) and d[key] is not None:
        d[key].append(elem)
    else:
        d[key] = [elem]


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
            logger.warning('problem urldecoding ' + pair)
    return ret


cipher=DES.new(settings.SECRET_KEY[0:8], DES.MODE_ECB)


def encrypt_and_encode(string):
    '''
    encrypts and encodes into base16
    the string must not contain trailing spaces (cause we need to add trailing spaces to have len % 8 = 0)
    '''
    while len(string) % 8 != 0:
        string += ' '
    encrypted = cipher.encrypt(string)
    return base64.b16encode(encrypted)


def decode_and_decrypt(string):
    encrypted = base64.b16decode(string)
    return cipher.decrypt(encrypted).strip()


def replace_non_ascii(str, with_char='_'):
    return ''.join([i if ord(i) < 128 else with_char for i in str])


def trim_digits(num, digits):
    digit_tens = pow(10, digits)
    trimmed = float(int(float(num) * digit_tens)) / digit_tens
    return trimmed


def str2hex(s):
    '''
    convert string to hex
    '''
    lst = []
    for ch in s:
        hv = hex(ord(ch)).replace('0x', '')
        if len(hv) == 1:
            hv = '0'+hv
        lst.append(hv)
    return reduce(lambda x,y:x+y, lst)


def hex2str(s):
    '''
    convert hex repr to string
    '''
    return s and chr(atoi(s[:2], base=16)) + hex2str(s[2:]) or ''


def empty_then_none(string):
    if string == '':
        return None
    else:
        return string


def none_then_empty(string):
    if string is None:
        return ''
    else:
        return string


def timestamp2datetime(ts):
    ts = float(ts)
    return datetime.datetime.fromtimestamp(ts)


def datetime2timestamp(dt):
    return long(time.mktime(dt.timetuple()))


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


def custom_range(l,range_first=None,range_last=None):
    if range_first is not None:
        range_first = int(range_first)
    if range_last is not None:
        range_last = int(range_last)
    if range_first is not None:
        if range_last is not None:
            return l[range_first:range_last]
        else:
            return l[range_first:]
    elif range_last is not None:
        return l[:range_last]
    else:
        return l


def get_pk(obj):
    return obj.pk if obj else None


def upload_pic(uploaded_file, toFile):
    destination = open(os.path.join(settings.MEDIA_ROOT, toFile), 'wb+')
    for chunk in uploaded_file.chunks():
        destination.write(chunk)
    destination.close()


def dist(lat0,lon0, lat1,lon1):
    dist2 = math.pow(float(lat1) - float(lat0), 2) + math.pow(float(lon1) - float(lon0),2)
    return math.sqrt(dist2)


def staff():
    return User.objects.filter(is_staff=1)


def staff_emails():
    emails = []
    for user in staff():
        if user.email:
            emails.append(user.email)
    return emails


def is_list_or_tuple(x):
    return isinstance(x, (list,tuple))


def list2comma_separated(the_list):
    if not the_list:
        return ''
    s = ''
    i = 0
    for e in the_list:
        if i != 0:
            s += ','
        i += 1
        s += str(e)
    return s


def load_class(full_class_string):
    '''
    dynamically load a class from a string
    '''
    class_data = full_class_string.split(".")
    module_path = ".".join(class_data[:-1])
    class_str = class_data[-1]

    module = importlib.import_module(module_path)
    # Finally, we retrieve the Class
    return getattr(module, class_str)


def setting(property_name, default=None):
    try:
        val = getattr(settings, property_name)
    except:
        print('WARNING:', property_name, ' not found in settings module')
        val = default
    return val


# TODO: parametrizar en settings
def is_site_view(path):
    if path.startswith(settings.MEDIA_URL) or path.startswith(settings.STATIC_URL):
        return False
    elif path.startswith('/admin'):
        return False
    elif path.startswith('/calendar'):
        return False
    else:
        return True