from django.core.management.base import BaseCommand
from marto_python.email.models import EmailMessage
from django.db.models import Q

class Command(BaseCommand):
    help = 'cleans email database'

    def handle(self, *args, **options):
        msgs = EmailMessage.objects.filter(
            Q(subject__contains='[Django] ERROR') |
            Q(subject__contains='[Django] CRITICAL'))

        if msgs.count() > 0:
            print(f'There are {msgs.count()} django error messages, cleaning:')
            print()
            for msg in msgs.all():
                print(' - ' + msg.subject[0:77])
                msg.delete()
        else:
            print(f'There are 0 django error messages.')

