# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('email', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='emailmessage',
            old_name='timestamp',
            new_name='created_on',
        ),
        migrations.AddField(
            model_name='emailmessage',
            name='sent',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='emailmessage',
            name='sent_on',
            field=models.DateTimeField(null=True),
        ),
    ]
