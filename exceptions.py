import sys
import logging
from django.views.debug import SafeExceptionReporterFilter

logger = logging.getLogger(__name__)


def log_exceptions(lggr=None, reraise=True):
    if not lggr: lggr = logger

    def logging_decorator(func):
        def exception_logging_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except:
                e = sys.exc_info()
                lggr.error(e[1], exc_info=True)
                if reraise:
                    raise
        return exception_logging_wrapper
    return logging_decorator


def error_view(message='Purposefully generated error for testing purposes'):
    def view_fn(request):
        raise(Exception(message))
    return view_fn


class NoSettingsReporterFilter(SafeExceptionReporterFilter):
    def get_safe_settings(self):
        return {'NO_SETTINGS': 'Sending settings has been disabled'}