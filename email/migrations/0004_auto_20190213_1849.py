# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-02-13 21:49
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('email', '0003_auto_20160820_1238'),
    ]

    operations = [
        migrations.RenameField(
            model_name='emailmessage',
            old_name='send_succesful',
            new_name='send_successful',
        ),
    ]
