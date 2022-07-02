from decimal import Decimal
from functools import reduce
from typing import Any, Optional


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
    except ValueError:
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


def human_list_str(strings: list[str], comma_str=', ', and_str=' and '):
    if not strings: return ''
    if len(strings) == 1:
        return strings[0]
    pre_and = strings[:-1]
    return comma_str.join(pre_and) + and_str + strings[-1]