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
                e = sys.exc_info()[2]
                logger.error(e, exc_info=True)
                raise
        return exception_logging_wrapper
    return logging_decorator

