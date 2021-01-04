from django.core.management.base import BaseCommand
from marto_python.email.models import EmailMessage
from django.db.models import Q

class Command(BaseCommand):
    help = 'cleans email database'

    def handle(self, *args, **options):
        msgs = EmailMessage.objects.filter(
            Q(subject__contains='[Django] ERROR') |
            Q(subject__contains='[Django] CRITICAL'))
        print(f'There are {msgs.count()} django error messages, cleaning...')
        for msg in msgs.all():
            print('deleting: ' + msg.subject[0:20])
            msg.delete()
