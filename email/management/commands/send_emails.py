import logging
logger = logging.getLogger(__name__)

from django.core.management.base import BaseCommand, CommandError

from marto_python.email.backend import DBEmailBackend

class Command(BaseCommand):
    help = 'tells db backend to send emails'

    def handle(self, *args, **options):
        logger.info('Telling db backend to send emails...')
        DBEmailBackend().send_all()
