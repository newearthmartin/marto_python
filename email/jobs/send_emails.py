import logging
from django_extensions.management.jobs import HourlyJob
from marto_python.email.backend import DBEmailBackend

logger = logging.getLogger(__name__)


class Job(HourlyJob):
    help = "try to send all queued emails"

    def execute(self):
        logger.info('Telling db backend to send emails...')
        DBEmailBackend().send_all()
