# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('email', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='emailmessage',
            name='fail_message',
            field=models.CharField(max_length=256, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='emailmessage',
            name='subject',
            field=models.CharField(max_length=256, null=True, blank=True),
        ),
    ]
