# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'Trip', fields ['user', 'date']
        db.delete_unique(u'dpnk_trip', ['user_id', 'date'])

        # Removing unique constraint on 'Answer', fields ['user', 'question']
        db.delete_unique(u'dpnk_answer', ['user_id', 'question_id'])

        # Removing unique constraint on 'CompetitionResult', fields ['userprofile', 'competition']
        db.delete_unique(u'dpnk_competitionresult', ['userprofile_id', 'competition_id'])

        # Deleting field 'Payment.user'
        db.delete_column(u'dpnk_payment', 'user_id')

        # Removing M2M table for field user_competitors on 'Competition'
        db.delete_table(db.shorten_name(u'dpnk_competition_user_competitors'))

        # Deleting field 'UserProfile.distance'
        db.delete_column(u'dpnk_userprofile', 'distance')

        # Deleting field 'UserProfile.approved_for_team'
        db.delete_column(u'dpnk_userprofile', 'approved_for_team')

        # Deleting field 'UserProfile.team'
        db.delete_column(u'dpnk_userprofile', 'team_id')

        # Deleting field 'UserProfile.t_shirt_size'
        db.delete_column(u'dpnk_userprofile', 't_shirt_size')

        # Deleting field 'CompetitionResult.userprofile'
        db.delete_column(u'dpnk_competitionresult', 'userprofile_id')

        # Adding unique constraint on 'CompetitionResult', fields ['user_attendance', 'competition']
        db.create_unique(u'dpnk_competitionresult', ['user_attendance_id', 'competition_id'])

        # Deleting field 'Answer.user'
        db.delete_column(u'dpnk_answer', 'user_id')

        # Adding unique constraint on 'Answer', fields ['user_attendance', 'question']
        db.create_unique(u'dpnk_answer', ['user_attendance_id', 'question_id'])

        # Deleting field 'Trip.user'
        db.delete_column(u'dpnk_trip', 'user_id')

        # Adding unique constraint on 'Trip', fields ['user_attendance', 'date']
        db.create_unique(u'dpnk_trip', ['user_attendance_id', 'date'])

        # Deleting field 'Team.coordinator'
        db.delete_column(u'dpnk_team', 'coordinator_id')


    def backwards(self, orm):
        # Removing unique constraint on 'Trip', fields ['user_attendance', 'date']
        db.delete_unique(u'dpnk_trip', ['user_attendance_id', 'date'])

        # Removing unique constraint on 'Answer', fields ['user_attendance', 'question']
        db.delete_unique(u'dpnk_answer', ['user_attendance_id', 'question_id'])

        # Removing unique constraint on 'CompetitionResult', fields ['user_attendance', 'competition']
        db.delete_unique(u'dpnk_competitionresult', ['user_attendance_id', 'competition_id'])

        # Adding field 'Payment.user'
        db.add_column(u'dpnk_payment', 'user',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='payments', null=True, to=orm['dpnk.UserProfile'], blank=True),
                      keep_default=False)

        # Adding M2M table for field user_competitors on 'Competition'
        m2m_table_name = db.shorten_name(u'dpnk_competition_user_competitors')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('competition', models.ForeignKey(orm[u'dpnk.competition'], null=False)),
            ('userprofile', models.ForeignKey(orm[u'dpnk.userprofile'], null=False))
        ))
        db.create_unique(m2m_table_name, ['competition_id', 'userprofile_id'])

        # Adding field 'UserProfile.distance'
        db.add_column(u'dpnk_userprofile', 'distance',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)

        # Adding field 'UserProfile.approved_for_team'
        db.add_column(u'dpnk_userprofile', 'approved_for_team',
                      self.gf('django.db.models.fields.CharField')(default='undecided', max_length=16),
                      keep_default=False)

        # Adding field 'UserProfile.team'
        db.add_column(u'dpnk_userprofile', 'team',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['dpnk.Team']),
                      keep_default=False)

        # Adding field 'UserProfile.t_shirt_size'
        db.add_column(u'dpnk_userprofile', 't_shirt_size',
                      self.gf('django.db.models.fields.CharField')(default='mL', max_length=16),
                      keep_default=False)

        # Adding field 'CompetitionResult.userprofile'
        db.add_column(u'dpnk_competitionresult', 'userprofile',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='competitions_results', null=True, to=orm['dpnk.UserProfile'], blank=True),
                      keep_default=False)

        # Adding unique constraint on 'CompetitionResult', fields ['userprofile', 'competition']
        db.create_unique(u'dpnk_competitionresult', ['userprofile_id', 'competition_id'])

        # Adding field 'Answer.user'
        db.add_column(u'dpnk_answer', 'user',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dpnk.UserProfile'], null=True, blank=True),
                      keep_default=False)

        # Adding unique constraint on 'Answer', fields ['user', 'question']
        db.create_unique(u'dpnk_answer', ['user_id', 'question_id'])

        # Adding field 'Trip.user'
        db.add_column(u'dpnk_trip', 'user',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=1, related_name='user_trips', to=orm['dpnk.UserProfile']),
                      keep_default=False)

        # Adding unique constraint on 'Trip', fields ['user', 'date']
        db.create_unique(u'dpnk_trip', ['user_id', 'date'])

        # Adding field 'Team.coordinator'
        db.add_column(u'dpnk_team', 'coordinator',
                      self.gf('django.db.models.fields.related.OneToOneField')(related_name='coordinated_team', unique=True, null=True, to=orm['dpnk.UserProfile'], blank=True),
                      keep_default=False)


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'dpnk.answer': {
            'Meta': {'ordering': "('user_attendance__team__subsidiary__city', 'pk')", 'unique_together': "(('user_attendance', 'question'),)", 'object_name': 'Answer'},
            'attachment': ('django.db.models.fields.files.FileField', [], {'max_length': '600'}),
            'choices': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['dpnk.Choice']", 'symmetrical': 'False'}),
            'comment': ('django.db.models.fields.TextField', [], {'max_length': '600', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'points_given': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dpnk.Question']"}),
            'user_attendance': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dpnk.UserAttendance']", 'null': 'True', 'blank': 'True'})
        },
        u'dpnk.campaign': {
            'Meta': {'object_name': 'Campaign'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60'})
        },
        u'dpnk.choice': {
            'Meta': {'unique_together': "(('choice_type', 'text'),)", 'object_name': 'Choice'},
            'choice_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'choices'", 'to': u"orm['dpnk.ChoiceType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'points': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '250', 'db_index': 'True'})
        },
        u'dpnk.choicetype': {
            'Meta': {'unique_together': "(('competition', 'name'),)", 'object_name': 'ChoiceType'},
            'competition': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dpnk.Competition']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '40', 'unique': 'True', 'null': 'True'}),
            'universal': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'dpnk.city': {
            'Meta': {'ordering': "('name',)", 'object_name': 'City'},
            'admission_fee': ('django.db.models.fields.PositiveIntegerField', [], {'default': '160'}),
            'city_admins': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'administrated_cities'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['dpnk.UserProfile']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'})
        },
        u'dpnk.company': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Company'},
            'address_city': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50'}),
            'address_district': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'address_psc': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'address_recipient': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50'}),
            'address_street': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50'}),
            'address_street_number': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '10'}),
            'ico': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60'})
        },
        u'dpnk.companyadmin': {
            'Meta': {'object_name': 'CompanyAdmin'},
            'administrated_company': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'company_admin'", 'unique': 'True', 'null': 'True', 'to': u"orm['dpnk.Company']"}),
            'company_admin_approved': ('django.db.models.fields.CharField', [], {'default': "'undecided'", 'max_length': '16'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mailing_id': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'motivation_company_admin': ('django.db.models.fields.TextField', [], {'default': "''", 'max_length': '5000', 'null': 'True', 'blank': 'True'}),
            'telephone': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'company_admin'", 'unique': 'True', 'to': u"orm['auth.User']"})
        },
        u'dpnk.competition': {
            'Meta': {'object_name': 'Competition'},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dpnk.Campaign']"}),
            'city': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dpnk.City']", 'null': 'True', 'blank': 'True'}),
            'company': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dpnk.Company']", 'null': 'True', 'blank': 'True'}),
            'company_competitors': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'competitions'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['dpnk.Company']"}),
            'competitor_type': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'date_from': ('django.db.models.fields.DateField', [], {'default': 'None'}),
            'date_to': ('django.db.models.fields.DateField', [], {'default': 'None'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40'}),
            'slug': ('django.db.models.fields.SlugField', [], {'default': "''", 'unique': 'True', 'max_length': '50'}),
            'team_competitors': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'competitions'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['dpnk.Team']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'url': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'user_attendance_competitors': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'competitions'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['dpnk.UserAttendance']"}),
            'without_admission': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'dpnk.competitionresult': {
            'Meta': {'unique_together': "(('user_attendance', 'competition'), ('team', 'competition'))", 'object_name': 'CompetitionResult'},
            'competition': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'results'", 'to': u"orm['dpnk.Competition']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'result': ('django.db.models.fields.FloatField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'competitions_results'", 'null': 'True', 'blank': 'True', 'to': u"orm['dpnk.Team']"}),
            'user_attendance': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['dpnk.UserAttendance']", 'null': 'True', 'blank': 'True'}),
        },
        u'dpnk.payment': {
            'Meta': {'object_name': 'Payment'},
            'amount': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'error': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order_id': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'pay_type': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'realized': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'session_id': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'trans_id': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'user_attendance': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'payments'", 'null': 'True', 'blank': 'True', 'to': u"orm['dpnk.UserAttendance']"})
        },
        u'dpnk.phase': {
            'Meta': {'object_name': 'Phase'},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dpnk.Campaign']"}),
            'date_from': ('django.db.models.fields.DateField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'date_to': ('django.db.models.fields.DateField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'registration'", 'unique': 'True', 'max_length': '16'})
        },
        u'dpnk.question': {
            'Meta': {'unique_together': "(('competition', 'order'),)", 'object_name': 'Question'},
            'choice_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dpnk.ChoiceType']"}),
            'competition': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dpnk.Competition']"}),
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {'max_length': '500'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'with_attachment': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'with_comment': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'dpnk.subsidiary': {
            'Meta': {'object_name': 'Subsidiary'},
            'address_city': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50'}),
            'address_district': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'address_psc': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'address_recipient': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50'}),
            'address_street': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50'}),
            'address_street_number': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '10'}),
            'city': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dpnk.City']"}),
            'company': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'subsidiaries'", 'to': u"orm['dpnk.Company']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'dpnk.team': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Team'},
            'coordinator_campaign': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'coordinated_team'", 'unique': 'True', 'null': 'True', 'to': u"orm['dpnk.UserAttendance']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invitation_token': ('django.db.models.fields.CharField', [], {'default': "''", 'unique': 'True', 'max_length': '100'}),
            'member_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'subsidiary': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'teams'", 'to': u"orm['dpnk.Subsidiary']"})
        },
        u'dpnk.trip': {
            'Meta': {'unique_together': "(('user_attendance', 'date'),)", 'object_name': 'Trip'},
            'date': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime.now'}),
            'distance_from': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'distance_to': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'trip_from': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'trip_to': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'user_attendance': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'user_trips'", 'null': 'True', 'blank': 'True', 'to': u"orm['dpnk.UserAttendance']"})
        },
        u'dpnk.userattendance': {
            'Meta': {'object_name': 'UserAttendance'},
            'approved_for_team': ('django.db.models.fields.CharField', [], {'default': "'undecided'", 'max_length': '16'}),
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dpnk.Campaign']"}),
            'distance': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            't_shirt_size': ('django.db.models.fields.CharField', [], {'default': "'mL'", 'max_length': '16'}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'users'", 'to': u"orm['dpnk.Team']"}),
            'userprofile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dpnk.UserProfile']", 'unique': 'True'})
        },
        u'dpnk.userprofile': {
            'Meta': {'ordering': "['user__last_name', 'user__first_name']", 'object_name': 'UserProfile'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "'cs'", 'max_length': '16'}),
            'mailing_id': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '128', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'telephone': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'userprofile'", 'unique': 'True', 'to': u"orm['auth.User']"})
        }
    }

    complete_apps = ['dpnk']
