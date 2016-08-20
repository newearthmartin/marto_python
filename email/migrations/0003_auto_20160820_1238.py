# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('email', '0002_auto_20160815_1134'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emailmessage',
            name='sent_on',
            field=models.DateTimeField(db_index=True, null=True, blank=True),
        ),
    ]
