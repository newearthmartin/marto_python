import sys
import logging
logger = logging.getLogger(__name__)

def log_exceptions(logger=None):
    if not logger:
        logger = logging.getLogger(__name__)
    def logging_decorator(func):
        def exception_logging_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except:
                e = sys.exc_info()
                logger.error(e[1], exc_info=True)
                raise
        return exception_logging_wrapper
    return logging_decorator
