# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Menu.seccion'
        db.add_column(u'pages_menu', 'seccion',
                      self.gf('django.db.models.fields.CharField')(default='PR', max_length=10),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Menu.seccion'
        db.delete_column(u'pages_menu', 'seccion')


    models = {
        u'pages.menu': {
            'Meta': {'object_name': 'Menu'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'indice': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'padre': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': u"orm['pages.Menu']"}),
            'pagina': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['pages.Pagina']", 'null': 'True', 'blank': 'True'}),
            'seccion': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'titulo': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'total_url': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
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