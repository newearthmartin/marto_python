import logging
import math
import datetime
import importlib

from types import BuiltinFunctionType, BuiltinMethodType,  FunctionType, MethodType, LambdaType
from functools import partial
from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.core.validators import validate_email
from .collection_utils import add_list_elem


logger = logging.getLogger(__name__)


class ErrorCode:
    def __init__(self, code, message):
        self.code = code
        self.message = message
    code = 0
    message = None


def add_message(request, message):
    add_list_elem(request.session, 'messages', message)


def as_datetime(ts):
    if ts < 0: return None
    return datetime.datetime.utcfromtimestamp(float(ts)).astimezone()


def as_timestamp(dt):
    return int(dt.timestamp())


def custom_range(l, range_first=None, range_last=None):
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


def daterange(start_date, end_date):
    delta = int((end_date - start_date).days)
    for n in range(0, delta):
        yield start_date + datetime.timedelta(n)


def days_difference(date_past, date_future):
    difference = date_future - date_past
    return difference.total_seconds() / datetime.timedelta(days=1).total_seconds()


def get_pk(obj):
    return obj.pk if obj else None


def dist(lat0, lon0, lat1, lon1):
    dist2 = math.pow(float(lat1) - float(lat0), 2) + math.pow(float(lon1) - float(lon0), 2)
    return math.sqrt(dist2)


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


def is_function(obj):
    return isinstance(obj, (BuiltinFunctionType, BuiltinMethodType,  FunctionType, MethodType, LambdaType, partial))


def get_full_class(obj):
    """
    return the fully qualified class name for the object
    """
    module = obj.__module__
    return ((module + '.') if module else '') + obj.__class__.__name__


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
        logger.debug(f'{property_name} not found in settings module')
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
