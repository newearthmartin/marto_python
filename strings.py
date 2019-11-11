import base64

from string import atoi
from decimal import Decimal
from Crypto.Cipher import DES

from django.conf import settings

cipher = DES.new(settings.SECRET_KEY[0:8], DES.MODE_ECB)


def encrypt_and_encode(string):
    """
    encrypts and encodes into base16
    the string must not contain trailing spaces (cause we need to add trailing spaces to have len % 8 = 0)
    """
    while len(string) % 8 != 0:
        string += ' '
    encrypted = cipher.encrypt(string)
    return base64.b16encode(encrypted)


def decode_and_decrypt(string):
    encrypted = base64.b16decode(string)
    return cipher.decrypt(encrypted).strip()


def replace_non_ascii(string, with_char='_'):
    return ''.join([i if ord(i) < 128 else with_char for i in string])


def trim_digits(num, digits):
    digit_tens = pow(10, digits)
    trimmed = float(int(float(num) * digit_tens)) / digit_tens
    return trimmed


def as_int(string):
    if not string: return None
    try:
        return int(string)
    except:
        return None


def to_decimal(num, decimal_places):
    places = Decimal(10) ** (-1 * decimal_places)
    return Decimal(num).quantize(places)


def str2hex(s):
    """
    convert string to hex
    """
    lst = []
    for ch in s:
        hv = hex(ord(ch)).replace('0x', '')
        if len(hv) == 1:
            hv = '0'+hv
        lst.append(hv)
    return reduce(lambda x, y: x + y, lst)


def hex2str(s):
    """
    convert hex repr to string
    """
    return s and chr(atoi(s[:2], base=16)) + hex2str(s[2:]) or ''


def empty_then_none(string):
    return string if string else None


def none_then_empty(string):
    return string if string else ''


def remove_zw(strng):
    return strng.replace('\u200B', '') \
                .replace('\u200C', '')


def cut_str(strng, length):
    l = len(strng)
    if l <= length:
        return strng
    else:
        return strng[:length-3] + '...'


def str_if(val, default_value=None):
    return str(val) if val else default_value