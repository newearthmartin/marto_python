import base64

from decimal import Decimal
from functools import reduce
from Crypto.Cipher import DES
from typing import Any, Optional

from django.conf import settings


def encrypt_and_encode(string: str) -> str:
    """
    encrypts and encodes into base16
    the string must not contain trailing spaces (cause we need to add trailing spaces to have len % 8 = 0)
    """
    string_bytes = string.encode('utf-8')
    excess = len(string_bytes) % 8
    if excess != 0:
        padding = ' ' * (8 - excess)
        string_bytes += padding.encode('utf-8')
    encrypted = _get_cipher().encrypt(string_bytes)
    return base64.b16encode(encrypted).decode('ascii')


def decode_and_decrypt(string: str) -> str:
    """
    we are assuming that the original data was utf-8
    """
    encrypted = base64.b16decode(string)
    return _get_cipher().decrypt(encrypted).decode('utf-8').strip()


def _get_cipher():
    return DES.new(settings.SECRET_KEY[0:8].encode('utf-8'), DES.MODE_ECB)


def replace_non_ascii(string: str, with_char: str = '_'):
    return ''.join([i if ord(i) < 128 else with_char for i in string])


def trim_digits(num: float, digits: int):
    digit_tens = pow(10, digits)
    trimmed = float(int(float(num) * digit_tens)) / digit_tens
    return trimmed


def as_int(string: str) -> Optional[int]:
    if not string: return None
    try:
        return int(string)
    except:
        return None


def to_decimal(num: float, decimal_places: int) -> Decimal:
    places = Decimal(10) ** (-1 * decimal_places)
    return Decimal(num).quantize(places)


def str2hex(s: str) -> str:
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


def hex2str(s: str) -> str:
    """
    convert hex repr to string
    """
    return s and chr(int(s[:2], base=16)) + hex2str(s[2:]) or ''


def empty_then_none(string: Optional[str]) -> Optional[str]:
    return string if string else None


def none_then_empty(string: Optional[str]) -> str:
    return string if string else ''


def remove_zw(string: str) -> str:
    return string.replace('\u200B', '') \
                 .replace('\u200C', '')


def cut_str(string: str, length: int) -> str:
    if len(string) <= length:
        return string
    return string[:length - 3] + '...'


def str_if(val: Optional[Any], default_value: Optional[str] = None) -> Optional[str]:
    return str(val) if val else default_value


def left_pad(s: str, total_digits: int, with_char: str = '0') -> str:
    padding = total_digits - len(s)
    if padding <= 0: return s
    return with_char * padding + s
