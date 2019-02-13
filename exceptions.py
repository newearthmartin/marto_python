import sys
import logging
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
