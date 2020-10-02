import logging
from django.core.management.base import BaseCommand
from marto_python.email.models import EmailMessage

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'cleans email database'

    def handle(self, *args, **options):
        msgs = EmailMessage.objects.filter(subject__contains='[Django] ERROR:').all()
        logger.info(f'there are {len(msgs)} django error messages, cleaning...')
        for msg in msgs:
            msg.delete()

