import logging
import math
import datetime
from typing import Type, Union
from datetime import timedelta, date, datetime
import importlib
import hashlib
import warnings

from types import BuiltinFunctionType, BuiltinMethodType,  FunctionType, MethodType, LambdaType
from functools import partial
from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.http import HttpRequest
from .collection_utils import add_list_elem


logger = logging.getLogger(__name__)


class ErrorCode:
    def __init__(self, code, message):
        self.code = code
        self.message = message
    code = 0
    message = None


def add_message(request: HttpRequest, message):
    add_list_elem(request.session, 'messages', message)


def as_datetime(ts):
    if ts < 0: return None
    return datetime.utcfromtimestamp(float(ts)).astimezone()


def as_timestamp(dt: datetime):
    return int(dt.timestamp())


def custom_range(lst: list, range_first=None, range_last=None):
    if range_first is not None:
        range_first = int(range_first)
    if range_last is not None:
        range_last = int(range_last)
    if range_first is not None:
        if range_last is not None:
            return lst[range_first:range_last]
        else:
            return lst[range_first:]
    elif range_last is not None:
        return lst[:range_last]
    else:
        return lst


def daterange(start_date: Union[date, datetime], end_date: Union[date, datetime]):
    delta = int((end_date - start_date).days)
    for n in range(0, delta):
        yield start_date + timedelta(n)


def days_difference(date_past: Union[date, datetime], date_future: Union[date, datetime]):
    difference = date_future - date_past
    return difference.total_seconds() / timedelta(days=1).total_seconds()


def get_pk(obj):
    return obj.pk if obj else None


def dist(lat0, lon0, lat1, lon1):
    dist2 = math.pow(float(lat1) - float(lat0), 2) + math.pow(float(lon1) - float(lon0), 2)
    return math.sqrt(dist2)


def staff():
    return User.objects.filter(is_staff=1)


def staff_emails() -> [str]:
    emails = []
    for user in staff():
        if user.email:
            emails.append(user.email)
    return emails


def is_valid_email(email: str) -> bool:
    try:
        validate_email(email)
        return True
    except forms.ValidationError:
        return False


def validate_field(o, field):
    try:
        o.full_clean()
        return True, None
    except ValidationError as e:
        field_msg = getattr(e, 'message_dict', {}).get(field, None)
        return False, field_msg or str(e)


def is_function(obj) -> bool:
    return isinstance(obj, (BuiltinFunctionType, BuiltinMethodType,  FunctionType, MethodType, LambdaType, partial))


def get_full_class(obj) -> str:
    """
    return the fully qualified class name for the object
    """
    module = obj.__module__
    return ((module + '.') if module else '') + obj.__class__.__name__


def load_class(full_classname: str) -> Type:
    """
    dynamically load a class from a string
    """
    class_data = full_classname.split(".")
    module_path = ".".join(class_data[:-1])
    class_str = class_data[-1]

    module = importlib.import_module(module_path)
    # Finally, we retrieve the Class
    return getattr(module, class_str)


def setting(property_name: str, default=None):
    try:
        return getattr(settings, property_name)
    except AttributeError:
        logger.debug(f'Setting {property_name} not found')
        return default


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


def change(obj, properties_new_vals):
    """
    Changes the given property to newVal.
    Returns true if the value actually changed
    """
    changed = False
    for prop, new_val in properties_new_vals.items():
        old_val = getattr(obj, prop)
        if old_val != new_val:
            setattr(obj, prop, new_val)
            changed = True
    return changed


def compose(f, g):
    def fog(*args, **kwargs):
        return f(g(*args, **kwargs))
    return fog


def get_sha256(data):
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.sha256(data).hexdigest()


def filter_warnings(func, filter_out_texts):
    with warnings.catch_warnings(record=True) as warnings_caught:
        warnings.simplefilter("always")
        rv= func()
        for warning in warnings_caught:
            if not any(t in str(warning.message) for t in filter_out_texts):
                logger.warning(warning.message)
    return rv
