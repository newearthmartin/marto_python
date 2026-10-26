import logging
from django_extensions.management.jobs import HourlyJob
from django.core import mail
from marto_email.backend import DBEmailBackend
from marto_python.util import setting, load_class
logger = logging.getLogger(__name__)


class Job(HourlyJob):
    help = "try to send all queued emails"

    def execute(self):
        logger.info('Telling db backend to send emails...')
        mail.mailers.default  # creates the DBEmailBackend instance
        if not DBEmailBackend.instance:
            logger.warning('DBEmailBackend is not instantiated')
            return
        # EMAIL_DB_BATCH_DISPATCH: dotted path of a callable taking a list of email ids
        # e.g. one that queues a celery task;
        dispatch_path = setting('EMAIL_DB_BATCH_DISPATCH')
        DBEmailBackend.instance.send_all(load_class(dispatch_path) if dispatch_path else None)
