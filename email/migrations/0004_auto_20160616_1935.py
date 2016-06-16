# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('email', '0003_auto_20160616_1747'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emailmessage',
            name='sent_on',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
