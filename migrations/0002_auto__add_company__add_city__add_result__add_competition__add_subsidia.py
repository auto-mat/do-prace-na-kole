# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Company'
        db.create_table('dpnk_company', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=60)),
            ('company_admin', self.gf('django.db.models.fields.related.OneToOneField')(blank=True, related_name='administrated_company', unique=True, null=True, to=orm['dpnk.UserProfile'])),
        ))
        db.send_create_signal('dpnk', ['Company'])

        # Adding model 'City'
        db.create_table('dpnk_city', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('recent_event', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('dpnk', ['City'])

        # Adding M2M table for field city_admins on 'City'
        db.create_table('dpnk_city_city_admins', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('city', models.ForeignKey(orm['dpnk.city'], null=False)),
            ('userprofile', models.ForeignKey(orm['dpnk.userprofile'], null=False))
        ))
        db.create_unique('dpnk_city_city_admins', ['city_id', 'userprofile_id'])

        # Adding model 'Result'
        db.create_table('dpnk_result', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('distance', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('trips_count', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('points', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('order', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('competition', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dpnk.Competition'])),
            ('company', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dpnk.Company'], null=True, blank=True)),
            ('team', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dpnk.Team'], null=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dpnk.UserProfile'], null=True, blank=True)),
        ))
        db.send_create_signal('dpnk', ['Result'])

        # Adding model 'Competition'
        db.create_table('dpnk_competition', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('competitor_type', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('city', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dpnk.City'], null=True, blank=True)),
            ('company', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dpnk.Company'], null=True, blank=True)),
        ))
        db.send_create_signal('dpnk', ['Competition'])

        # Adding M2M table for field user_competitors on 'Competition'
        db.create_table('dpnk_competition_user_competitors', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('competition', models.ForeignKey(orm['dpnk.competition'], null=False)),
            ('userprofile', models.ForeignKey(orm['dpnk.userprofile'], null=False))
        ))
        db.create_unique('dpnk_competition_user_competitors', ['competition_id', 'userprofile_id'])

        # Adding M2M table for field team_competitors on 'Competition'
        db.create_table('dpnk_competition_team_competitors', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('competition', models.ForeignKey(orm['dpnk.competition'], null=False)),
            ('team', models.ForeignKey(orm['dpnk.team'], null=False))
        ))
        db.create_unique('dpnk_competition_team_competitors', ['competition_id', 'team_id'])

        # Adding model 'Subsidiary'
        db.create_table('dpnk_subsidiary', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=60)),
            ('address', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('company', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dpnk.Company'])),
            ('city', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dpnk.City'])),
        ))
        db.send_create_signal('dpnk', ['Subsidiary'])

        # Adding field 'Question.with_attachment'
        db.add_column('dpnk_question', 'with_attachment',
                      self.gf('django.db.models.fields.BooleanField')(default=True),
                      keep_default=False)

        # Adding field 'Question.competition'
        db.add_column('dpnk_question', 'competition',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dpnk.Competition'], null=True, blank=True),
                      keep_default=False)

        # Adding field 'Team.subsidiary'
        db.add_column('dpnk_team', 'subsidiary',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=0, to=orm['dpnk.Subsidiary']),
                      keep_default=False)

        # Adding field 'Team.coordinator'
        db.add_column('dpnk_team', 'coordinator',
                      self.gf('django.db.models.fields.related.OneToOneField')(blank=True, related_name='coordinated_team', unique=True, null=True, to=orm['dpnk.UserProfile']),
                      keep_default=False)

        # Adding field 'UserProfile.wants_to_be_paid'
        db.add_column('dpnk_userprofile', 'wants_to_be_paid',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'UserProfile.company_pays'
        db.add_column('dpnk_userprofile', 'company_pays',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'UserProfile.libero'
        db.add_column('dpnk_userprofile', 'libero',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'Answer.result'
        db.add_column('dpnk_answer', 'result',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dpnk.Result'], null=True),
                      keep_default=False)

        # Adding field 'Answer.points_given'
        db.add_column('dpnk_answer', 'points_given',
                      self.gf('django.db.models.fields.IntegerField')(default=0, null=True, blank=True),
                      keep_default=False)


        # Changing field 'Answer.user'
        db.alter_column('dpnk_answer', 'user_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dpnk.UserProfile'], null=True))
        # Adding field 'Trip.distance_to'
        db.add_column('dpnk_trip', 'distance_to',
                      self.gf('django.db.models.fields.IntegerField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'Trip.distance_from'
        db.add_column('dpnk_trip', 'distance_from',
                      self.gf('django.db.models.fields.IntegerField')(null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting model 'Company'
        db.delete_table('dpnk_company')

        # Deleting model 'City'
        db.delete_table('dpnk_city')

        # Removing M2M table for field city_admins on 'City'
        db.delete_table('dpnk_city_city_admins')

        # Deleting model 'Result'
        db.delete_table('dpnk_result')

        # Deleting model 'Competition'
        db.delete_table('dpnk_competition')

        # Removing M2M table for field user_competitors on 'Competition'
        db.delete_table('dpnk_competition_user_competitors')

        # Removing M2M table for field team_competitors on 'Competition'
        db.delete_table('dpnk_competition_team_competitors')

        # Deleting model 'Subsidiary'
        db.delete_table('dpnk_subsidiary')

        # Deleting field 'Question.with_attachment'
        db.delete_column('dpnk_question', 'with_attachment')

        # Deleting field 'Question.competition'
        db.delete_column('dpnk_question', 'competition_id')

        # Deleting field 'Team.subsidiary'
        db.delete_column('dpnk_team', 'subsidiary_id')

        # Deleting field 'Team.coordinator'
        db.delete_column('dpnk_team', 'coordinator_id')

        # Deleting field 'UserProfile.wants_to_be_paid'
        db.delete_column('dpnk_userprofile', 'wants_to_be_paid')

        # Deleting field 'UserProfile.company_pays'
        db.delete_column('dpnk_userprofile', 'company_pays')

        # Deleting field 'UserProfile.libero'
        db.delete_column('dpnk_userprofile', 'libero')

        # Deleting field 'Answer.result'
        db.delete_column('dpnk_answer', 'result_id')

        # Deleting field 'Answer.points_given'
        db.delete_column('dpnk_answer', 'points_given')


        # Changing field 'Answer.user'
        db.alter_column('dpnk_answer', 'user_id', self.gf('django.db.models.fields.related.ForeignKey')(default=0, to=orm['dpnk.UserProfile']))
        # Deleting field 'Trip.distance_to'
        db.delete_column('dpnk_trip', 'distance_to')

        # Deleting field 'Trip.distance_from'
        db.delete_column('dpnk_trip', 'distance_from')


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
            'points_given': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dpnk.Question']"}),
            'result': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dpnk.Result']", 'null': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dpnk.UserProfile']", 'null': 'True'})
        },
        'dpnk.choice': {
            'Meta': {'object_name': 'Choice'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'points': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dpnk.Question']"}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '300'})
        },
        'dpnk.city': {
            'Meta': {'object_name': 'City'},
            'city_admins': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'administrated_cities'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['dpnk.UserProfile']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'recent_event': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        },
        'dpnk.company': {
            'Meta': {'object_name': 'Company'},
            'company_admin': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'administrated_company'", 'unique': 'True', 'null': 'True', 'to': "orm['dpnk.UserProfile']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'})
        },
        'dpnk.competition': {
            'Meta': {'object_name': 'Competition'},
            'city': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dpnk.City']", 'null': 'True', 'blank': 'True'}),
            'company': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dpnk.Company']", 'null': 'True', 'blank': 'True'}),
            'competitor_type': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'team_competitors': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'competitions'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['dpnk.Team']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'user_competitors': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'competitions'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['dpnk.UserProfile']"})
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
            'competition': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dpnk.Competition']", 'null': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'questionaire': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'text': ('django.db.models.fields.TextField', [], {'max_length': '500'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'with_attachment': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'with_comment': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        'dpnk.result': {
            'Meta': {'object_name': 'Result'},
            'company': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dpnk.Company']", 'null': 'True', 'blank': 'True'}),
            'competition': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dpnk.Competition']"}),
            'distance': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'points': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dpnk.Team']", 'null': 'True', 'blank': 'True'}),
            'trips_count': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dpnk.UserProfile']", 'null': 'True', 'blank': 'True'})
        },
        'dpnk.subsidiary': {
            'Meta': {'object_name': 'Subsidiary'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'city': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dpnk.City']"}),
            'company': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dpnk.Company']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'})
        },
        'dpnk.team': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Team'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'company': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'coordinator': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'coordinated_team'", 'unique': 'True', 'null': 'True', 'to': "orm['dpnk.UserProfile']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'subsidiary': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dpnk.Subsidiary']"})
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
            'distance_from': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'distance_to': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'trip_from': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'trip_to': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dpnk.UserProfile']", 'null': 'True', 'blank': 'True'})
        },
        'dpnk.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'company_pays': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'distance': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'firstname': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'libero': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'surname': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dpnk.Team']"}),
            'telephone': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'trips': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'}),
            'wants_to_be_paid': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
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