# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('email', '0004_auto_20160616_1935'),
    ]

    operations = [
        migrations.AddField(
            model_name='emailmessage',
            name='failed_send',
            field=models.BooleanField(default=False),
        ),
    ]
