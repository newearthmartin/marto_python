# Generated by Django 3.1.2 on 2021-01-18 14:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('email', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emailmessage',
            name='fail_message',
            field=models.CharField(blank=True, max_length=1024, null=True),
        ),
    ]
