# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('email', '0002_auto_20160618_2340'),
    ]

    operations = [
        migrations.RenameField(
            model_name='emailmessage',
            old_name='failed_send',
            new_name='send_succesful',
        ),
        migrations.RemoveField(
            model_name='emailmessage',
            name='email_object',
        ),
        migrations.AddField(
            model_name='emailmessage',
            name='email_dump',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='emailmessage',
            name='from_email',
            field=models.CharField(max_length=256),
        ),
    ]
