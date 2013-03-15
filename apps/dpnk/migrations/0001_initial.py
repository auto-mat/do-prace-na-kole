# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Team'
        db.create_table('dpnk_team', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50)),
            ('company', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('address', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('city', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=20)),
        ))
        db.send_create_signal('dpnk', ['Team'])

        # Adding model 'UserProfile'
        db.create_table('dpnk_userprofile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('firstname', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('surname', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], unique=True)),
            ('distance', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('telephone', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('team', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dpnk.Team'])),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('trips', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
        ))
        db.send_create_signal('dpnk', ['UserProfile'])

        # Adding model 'Payment'
        db.create_table('dpnk_payment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dpnk.UserProfile'])),
            ('order_id', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('session_id', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('trans_id', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('amount', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=500, null=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('realized', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('pay_type', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('status', self.gf('django.db.models.fields.PositiveIntegerField')(max_length=50, null=True, blank=True)),
            ('error', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('dpnk', ['Payment'])

        # Adding model 'Voucher'
        db.create_table('dpnk_voucher', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dpnk.UserProfile'], null=True, blank=True)),
        ))
        db.send_create_signal('dpnk', ['Voucher'])

        # Adding model 'Trip'
        db.create_table('dpnk_trip', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dpnk.UserProfile'], null=True, blank=True)),
            ('date', self.gf('django.db.models.fields.DateField')(default=datetime.datetime.now)),
            ('trip_to', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('trip_from', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('dpnk', ['Trip'])

        # Adding model 'Question'
        db.create_table('dpnk_question', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('text', self.gf('django.db.models.fields.TextField')(max_length=500)),
            ('date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('with_comment', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('questionaire', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('order', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('dpnk', ['Question'])

        # Adding model 'Choice'
        db.create_table('dpnk_choice', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dpnk.Question'])),
            ('text', self.gf('django.db.models.fields.CharField')(max_length=300)),
            ('points', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('dpnk', ['Choice'])

        # Adding model 'Answer'
        db.create_table('dpnk_answer', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dpnk.UserProfile'])),
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dpnk.Question'])),
            ('comment', self.gf('django.db.models.fields.TextField')(max_length=600, null=True, blank=True)),
        ))
        db.send_create_signal('dpnk', ['Answer'])

        # Adding M2M table for field choices on 'Answer'
        db.create_table('dpnk_answer_choices', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('answer', models.ForeignKey(orm['dpnk.answer'], null=False)),
            ('choice', models.ForeignKey(orm['dpnk.choice'], null=False))
        ))
        db.create_unique('dpnk_answer_choices', ['answer_id', 'choice_id'])


    def backwards(self, orm):
        # Deleting model 'Team'
        db.delete_table('dpnk_team')

        # Deleting model 'UserProfile'
        db.delete_table('dpnk_userprofile')

        # Deleting model 'Payment'
        db.delete_table('dpnk_payment')

        # Deleting model 'Voucher'
        db.delete_table('dpnk_voucher')

        # Deleting model 'Trip'
        db.delete_table('dpnk_trip')

        # Deleting model 'Question'
        db.delete_table('dpnk_question')

        # Deleting model 'Choice'
        db.delete_table('dpnk_choice')

        # Deleting model 'Answer'
        db.delete_table('dpnk_answer')

        # Removing M2M table for field choices on 'Answer'
        db.delete_table('dpnk_answer_choices')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'dpnk.answer': {
            'Meta': {'object_name': 'Answer'},
            'choices': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['dpnk.Choice']", 'symmetrical': 'False'}),
            'comment': ('django.db.models.fields.TextField', [], {'max_length': '600', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dpnk.Question']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dpnk.UserProfile']"})
        },
        'dpnk.choice': {
            'Meta': {'object_name': 'Choice'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'points': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dpnk.Question']"}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '300'})
        },
        'dpnk.payment': {
            'Meta': {'object_name': 'Payment'},
            'amount': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True'}),
            'error': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order_id': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'pay_type': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'realized': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'session_id': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'status': ('django.db.models.fields.PositiveIntegerField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'trans_id': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dpnk.UserProfile']"})
        },
        'dpnk.question': {
            'Meta': {'object_name': 'Question'},
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'questionaire': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'text': ('django.db.models.fields.TextField', [], {'max_length': '500'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'with_comment': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        'dpnk.team': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Team'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'company': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'dpnk.teamresults': {
            'Meta': {'object_name': 'TeamResults', 'db_table': "'dpnk_v_team_results'", 'managed': 'False'},
            'city': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'company': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'distance': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'id': ('django.db.models.fields.PositiveIntegerField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'persons': ('django.db.models.fields.IntegerField', [], {}),
            'trips': ('django.db.models.fields.IntegerField', [], {}),
            'trips_per_person': ('django.db.models.fields.FloatField', [], {})
        },
        'dpnk.trip': {
            'Meta': {'object_name': 'Trip'},
            'date': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'trip_from': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'trip_to': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dpnk.UserProfile']", 'null': 'True', 'blank': 'True'})
        },
        'dpnk.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'distance': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'firstname': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'surname': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dpnk.Team']"}),
            'telephone': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'trips': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'dpnk.userresults': {
            'Meta': {'object_name': 'UserResults', 'db_table': "'dpnk_v_user_results'", 'managed': 'False'},
            'city': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'company': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'distance': ('django.db.models.fields.IntegerField', [], {}),
            'firstname': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'id': ('django.db.models.fields.PositiveIntegerField', [], {'primary_key': 'True'}),
            'surname': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'team': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'team_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'trips': ('django.db.models.fields.IntegerField', [], {})
        },
        'dpnk.voucher': {
            'Meta': {'object_name': 'Voucher'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dpnk.UserProfile']", 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['dpnk']