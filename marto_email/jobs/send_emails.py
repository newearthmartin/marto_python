import logging
from django.core import mail
from django_extensions.management.jobs import HourlyJob
from marto_email.backend import DBEmailBackend, StackedEmailBackend
logger = logging.getLogger(__name__)


class Job(HourlyJob):
    help = "try to send all queued emails"

    def execute(self):
        logger.info('Telling db backend to send emails...')
        mail.get_connection()
        if not DBEmailBackend.instance:
            logger.warning('DBEmailBackend is not instantiated')
            return
        DBEmailBackend.instance.send_all()
