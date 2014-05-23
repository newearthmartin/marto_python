# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'EmailMessage'
        db.create_table(u'email_emailmessage', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('from_email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
            ('to', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('cc', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('bcc', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('subject', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('body', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'email', ['EmailMessage'])


    def backwards(self, orm):
        # Deleting model 'EmailMessage'
        db.delete_table(u'email_emailmessage')


    models = {
        u'email.emailmessage': {
            'Meta': {'object_name': 'EmailMessage'},
            'bcc': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'body': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'cc': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'from_email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'to': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['email']