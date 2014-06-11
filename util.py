# encoding: utf-8

import math
import os
import urllib
import importlib
import time,datetime
from string import atoi
from django.conf import settings
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.core.mail.message import EmailMultiAlternatives
from Crypto.Cipher import DES
import base64

class ErrorCode:
    def __init__(self, code, message):
        self.code = code
        self.message = message
    code = 0
    message = None

def addMessage(request, message):
    addListElem(request.session, 'messages', message)

def addListElem(d, key, elem):
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
            print 'problem urldecoding ' + pair
    return ret

cipher=DES.new(settings.SECRET_KEY[0:8], DES.MODE_ECB)
#encrypts and encodes into base16
#the string must not contain trailing spaces (cause we need to add trailing spaces to have len % 8 = 0)
def encryptAndEncode(string):
    while len(string) % 8 != 0:
        string += ' '
    encrypted = cipher.encrypt(string)
    return base64.b16encode(encrypted)

def decodeAndDecrypt(string):
    encrypted = base64.b16decode(string)
    return cipher.decrypt(encrypted).strip()


def trimDigits(num, digits):
    digitTens = pow(10, digits)
    trimmed = float(int(float(num) * digitTens)) / digitTens
    return trimmed

#convert string to hex
def str2hex(s):
    lst = []
    for ch in s:
        hv = hex(ord(ch)).replace('0x', '')
        if len(hv) == 1:
            hv = '0'+hv
        lst.append(hv)
    return reduce(lambda x,y:x+y, lst)

#convert hex repr to string
def hex2str(s):
    return s and chr(atoi(s[:2], base=16)) + hex2str(s[2:]) or ''

def emptyThenNone(string):
    if string == '':
        return None
    else:
        return string
def noneThenEmpty(string):
    if string is None:
        return ''
    else:
        return string

def timestamp2datetime(ts):
    ts = float(ts)
    return datetime.datetime.fromtimestamp(ts)

def datetime2timestamp(dt):
    return long(time.mktime(dt.timetuple()))

    
def getParam(request, paramName, emptyValid=False, default=None, unicodeEncoding=True):
    val = default
    if paramName in request.GET:
        tempVal = request.GET[paramName]
        if emptyValid or len(tempVal) > 0:
            val = tempVal
    if unicodeEncoding and val is not None:
        val = unicode(val)
    return val

def postParam(request, paramName, emptyValid=False, default=None, unicodeEncoding=True):
    val = default
    if paramName in request.POST:
        tempVal = request.POST[paramName]
        if emptyValid or len(tempVal) > 0:
            val = tempVal
    if unicodeEncoding and val is not None:
        val = unicode(val)
    return val

def customRange(l,rangeFirst=None,rangeLast=None):
    if rangeFirst is not None:
        rangeFirst = int(rangeFirst)
    if rangeLast is not None:
        rangeLast = int(rangeLast)
    if rangeFirst is not None:
        if rangeLast is not None:
            return l[rangeFirst:rangeLast]
        else:
            return l[rangeFirst:]
    elif rangeLast is not None:
        return l[:rangeLast]
    else:
        return l

def getPk(obj):
    if obj is None:
        return None
    else:
        return obj.pk
    
def uploadPic(uploadedFile, toFile):
    destination = open(os.path.join(settings.MEDIA_ROOT, toFile), 'wb+')
    for chunk in uploadedFile.chunks():
        destination.write(chunk)
    destination.close()

def dist(lat0,lon0, lat1,lon1):
    dist2 = math.pow(float(lat1) - float(lat0), 2) + math.pow(float(lon1) - float(lon0),2)
    return math.sqrt(dist2)

def staff():
    return User.objects.filter(is_staff=1)

def staffEmails():
    emails = []
    for user in staff():
        if user.email:
            emails.append(user.email)
    return emails

def isListOrTuple(x):
    return isinstance(x, (list,tuple))

def toCommaSeparatedString(list):
    if not list:
        return ''
    s = ''
    i = 0
    for e in list:
        if i != 0:
            s += ','
        i += 1
        s += str(e)
    return s


def load_class(full_class_string):
    """
    dynamically load a class from a string
    """
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