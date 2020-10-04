# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Menu',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('titulo', models.CharField(max_length=255)),
                ('seccion', models.CharField(max_length=10, choices=[(b'PR', 'men\xfa principal'), (b'FO', 'pie de p\xe1gina')])),
                ('indice', models.IntegerField(default=0)),
                ('url', models.CharField(max_length=255, null=True, blank=True)),
                ('total_url', models.CharField(max_length=255, null=True, blank=True)),
                ('padre', models.ForeignKey(related_name=b'children', blank=True, to='pages.Menu', null=True)),
            ],
            options={
                'verbose_name': 'men\xfa',
                'verbose_name_plural': 'men\xfas',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Pagina',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.CharField(unique=True, max_length=255)),
                ('titulo', models.CharField(max_length=255)),
                ('contenido', models.TextField()),
                ('extra_css', models.CharField(max_length=255, null=True, blank=True)),
            ],
            options={
                'verbose_name': 'p\xe1gina',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='menu',
            name='pagina',
            field=models.ForeignKey(blank=True, to='pages.Pagina', null=True),
            preserve_default=True,
        ),
    ]
