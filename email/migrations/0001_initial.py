# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

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
                ('sent_on', models.DateTimeField(null=True, blank=True)),
                ('failed_send', models.BooleanField(default=False)),
                ('email_object', models.TextField(null=True, blank=True)),
            ],
        ),
    ]
