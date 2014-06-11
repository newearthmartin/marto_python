# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Menu'
        db.create_table(u'pages_menu', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('titulo', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('padre', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='children', null=True, to=orm['pages.Menu'])),
            ('indice', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('pagina', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='menu', null=True, to=orm['pages.Pagina'])),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('totalUrl', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
        ))
        db.send_create_signal(u'pages', ['Menu'])

        # Adding model 'Pagina'
        db.create_table(u'pages_pagina', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('url', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('titulo', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('contenido', self.gf('django.db.models.fields.TextField')()),
            ('extra_css', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
        ))
        db.send_create_signal(u'pages', ['Pagina'])


    def backwards(self, orm):
        # Deleting model 'Menu'
        db.delete_table(u'pages_menu')

        # Deleting model 'Pagina'
        db.delete_table(u'pages_pagina')


    models = {
        u'pages.menu': {
            'Meta': {'object_name': 'Menu'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'indice': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'padre': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': u"orm['pages.Menu']"}),
            'pagina': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'menu'", 'null': 'True', 'to': u"orm['pages.Pagina']"}),
            'titulo': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'totalUrl': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        u'pages.pagina': {
            'Meta': {'object_name': 'Pagina'},
            'contenido': ('django.db.models.fields.TextField', [], {}),
            'extra_css': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'titulo': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'url': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        }
    }

    complete_apps = ['pages']