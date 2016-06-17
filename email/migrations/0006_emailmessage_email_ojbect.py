# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('email', '0005_emailmessage_failed_send'),
    ]

    operations = [
        migrations.AddField(
            model_name='emailmessage',
            name='email_ojbect',
            field=models.TextField(null=True),
        ),
    ]
