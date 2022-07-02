from django.core.management.base import BaseCommand
from marto_python.email.models import EmailMessage
from django.db.models import Q


def filter_error_emails(queryset, filter_not_exclude=True):
    query = Q(subject__contains='[Django] ERROR') | Q(subject__contains='[Django] CRITICAL')
    return queryset.filter(query) if filter_not_exclude else queryset.exclude(query)


class Command(BaseCommand):
    help = 'cleans email database'

    def handle(self, *args, **options):
        msgs = filter_error_emails(EmailMessage.objects)
        if msgs.count() > 0:
            print(f'There are {msgs.count()} django error messages, cleaning:')
            print()
            for msg in msgs.all():
                print(' - ' + msg.subject[0:77])
                msg.delete()
        else:
            print(f'There are 0 django error messages.')
