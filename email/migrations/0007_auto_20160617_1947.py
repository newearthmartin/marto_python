# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('email', '0006_emailmessage_email_ojbect'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='emailmessage',
            name='email_ojbect',
        ),
        migrations.AddField(
            model_name='emailmessage',
            name='email_object',
            field=models.TextField(null=True, blank=True),
        ),
    ]
