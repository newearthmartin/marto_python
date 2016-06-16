# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations, models

from marto_python.email.models import EmailMessage

def forwards(apps, schema_editor):
    for email in EmailMessage.objects.all():
        email.sent = True
        email.save()

class Migration(migrations.Migration):
    dependencies = [
        ('email', '0002_auto_20160616_1725'),
    ]
    operations = [
        migrations.RunPython(forwards)
    ]
