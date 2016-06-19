# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('email', '0003_auto_20160619_0150'),
    ]

    operations = [
        migrations.AddField(
            model_name='emailmessage',
            name='email_class',
            field=models.CharField(default='', max_length=256),
            preserve_default=False,
        ),
    ]
