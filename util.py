# encoding: utf-8

import math
import os
import urllib
import importlib
import base64
import time,datetime

from pytz import timezone as pytz_timezone
from string import atoi
from decimal import Decimal
from threading import Thread
from Crypto.Cipher import DES

from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.core.validators import validate_email


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

def to_decimal(num, decimal_places):
    PLACES = Decimal(10) ** (-1 * decimal_places)
    return Decimal(num).quantize(PLACES)

def get_or_add_new(dict, key, new_elem_func):
    if key not in dict:
        dict[key] = new_elem_func()
    return dict[key]

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

def make_tz_aware(dattetime, tz=None):
    '''
    makes the datetime tz aware, if no tz is passed, uses the tz from settings
    '''
    if not tz:
        tz = pytz_timezone(settings.TIME_ZONE)
    return tz.localize(dattetime)


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
    if obj is None:
        return None
    else:
        return obj.pk

def upload_pic(uploaded_file, toFile):
    destination = open(os.path.join(settings.MEDIA_ROOT, toFile), 'wb+')
    for chunk in uploaded_file.chunks():
        destination.write(chunk)
    destination.close()

def dist(lat0,lon0, lat1,lon1):
    dist2 = math.pow(float(lat1) - float(lat0), 2) + math.pow(float(lon1) - float(lon0),2)
    return math.sqrt(dist2)

def read_lines(file, remove_empty=True):
    lines = file.read().splitlines()
    lines = map(lambda s: s.strip(), lines)
    if remove_empty: filter(lambda s: s != '', lines)
    return lines

def staff():
    return User.objects.filter(is_staff=1)

def staff_emails():
    emails = []
    for user in staff():
        if user.email:
            emails.append(user.email)
    return emails

def is_valid_email(email):
    try:
        validate_email(email)
        return True
    except forms.ValidationError:
        return False

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

def get_full_class(object):
    '''
    return the fully qualified class name for the object
    '''
    module = object.__module__
    return ((module + '.') if module else '') + object.__class__.__name__


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
        print 'WARNING:', property_name, ' not found in settings module'
        val = default
    return val

#TODO: parametrizar en settings
def is_site_view(path):
    if path.startswith(settings.MEDIA_URL) or path.startswith(settings.STATIC_URL):
        return False
    elif path.startswith('/admin'):
        return False
    elif path.startswith('/calendar'):
        return False
    else:
        return True

def dict_encode(obj, encoder=None):
    '''
    useful for serializing objects to JSON
    use: json.dumps(dict_encode(obj,encoder=some_encoder_func))
    '''
    if obj == None: return None
    if type(obj) == dict:
        rv = {}
        for k, v in obj.iteritems():
            rv[k] = dict_encode(v, encoder)
        return rv
    if hasattr(obj, '__iter__'):
        rv = []
        for elem in obj:
            rv.append(dict_encode(elem, encoder))
        return rv
    if not hasattr(obj, '__dict__'):
        return obj
    if encoder:
        val = encoder(obj)
        if val: return dict_encode(val, encoder)
    raise(Exception('Could not encode %s to dictionary' % type(obj)))

class RunInThread:
    '''
    decorator to run the method in a thread
    '''
    def __init__(self, f):
        self.f = f
    def __call__(self, *args, **kwargs):
        Thread(target=lambda:self.f(*args, **kwargs)).start()
