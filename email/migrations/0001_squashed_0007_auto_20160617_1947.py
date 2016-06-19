# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


# Functions from the following migrations need manual copying.
# Move them and any dependencies into this file, then update the
# RunPython operations to refer to the local versions:
# marto_python.email.migrations.0003_auto_20160616_1747

class Migration(migrations.Migration):

    replaces = [(b'email', '0001_initial'), (b'email', '0002_auto_20160616_1725'), (b'email', '0003_auto_20160616_1747'), (b'email', '0004_auto_20160616_1935'), (b'email', '0005_emailmessage_failed_send'), (b'email', '0006_emailmessage_email_ojbect'), (b'email', '0007_auto_20160617_1947')]

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='EmailMessage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('from_email', models.EmailField(max_length=254)),
                ('to', models.TextField(null=True, blank=True)),
                ('cc', models.TextField(null=True, blank=True)),
                ('bcc', models.TextField(null=True, blank=True)),
                ('subject', models.CharField(max_length=255, null=True, blank=True)),
                ('body', models.TextField(null=True, blank=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('sent', models.BooleanField(default=False)),
                ('sent_on', models.DateTimeField(null=True)),
            ],
        ),
        migrations.RunPython(
            code=marto_python.email.migrations.0003_auto_20160616_1747.forwards,
        ),
        migrations.AlterField(
            model_name='emailmessage',
            name='sent_on',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='emailmessage',
            name='failed_send',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='emailmessage',
            name='email_object',
            field=models.TextField(null=True, blank=True),
        ),
    ]
