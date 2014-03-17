# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'Team', fields ['name']
        db.delete_unique(u'dpnk_team', ['name'])

        # Adding unique constraint on 'Team', fields ['name', 'campaign']
        db.create_unique(u'dpnk_team', ['name', 'campaign_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'Team', fields ['name', 'campaign']
        db.delete_unique(u'dpnk_team', ['name', 'campaign_id'])

        # Adding unique constraint on 'Team', fields ['name']
        db.create_unique(u'dpnk_team', ['name'])


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
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
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
            'email_footer': ('django.db.models.fields.TextField', [], {'default': "''", 'max_length': '5000', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mailing_list_enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'mailing_list_id': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '60', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60'}),
            'slug': ('django.db.models.fields.SlugField', [], {'default': "''", 'unique': 'True', 'max_length': '50'})
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
            'city_admins': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'administrated_cities'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['dpnk.UserProfile']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'})
        },
        u'dpnk.cityincampaign': {
            'Meta': {'ordering': "('city__name',)", 'unique_together': "(('city', 'campaign'),)", 'object_name': 'CityInCampaign'},
            'admission_fee': ('django.db.models.fields.PositiveIntegerField', [], {'default': '160'}),
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dpnk.Campaign']"}),
            'city': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dpnk.City']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'dpnk.commontransaction': {
            'Meta': {'object_name': 'CommonTransaction', '_ormbases': [u'dpnk.Transaction']},
            u'transaction_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['dpnk.Transaction']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'dpnk.company': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Company'},
            'address_city': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50'}),
            'address_district': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'address_psc': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'address_recipient': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'address_street': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50'}),
            'address_street_number': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '10'}),
            'ico': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60'})
        },
        u'dpnk.companyadmin': {
            'Meta': {'unique_together': "(('user', 'campaign'), ('administrated_company', 'campaign'))", 'object_name': 'CompanyAdmin'},
            'administrated_company': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'company_admin'", 'null': 'True', 'to': u"orm['dpnk.Company']"}),
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dpnk.Campaign']"}),
            'company_admin_approved': ('django.db.models.fields.CharField', [], {'default': "'undecided'", 'max_length': '16'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'motivation_company_admin': ('django.db.models.fields.TextField', [], {'default': "''", 'max_length': '5000', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'company_admin'", 'to': u"orm['auth.User']"})
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
            'user_attendance': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'competitions_results'", 'null': 'True', 'blank': 'True', 'to': u"orm['dpnk.UserAttendance']"})
        },
        u'dpnk.packagetransaction': {
            'Meta': {'object_name': 'PackageTransaction', '_ormbases': [u'dpnk.Transaction']},
            u'transaction_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['dpnk.Transaction']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'dpnk.payment': {
            'Meta': {'object_name': 'Payment', '_ormbases': [u'dpnk.Transaction']},
            'amount': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'error': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'order_id': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'pay_type': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'session_id': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'trans_id': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            u'transaction_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['dpnk.Transaction']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'dpnk.phase': {
            'Meta': {'unique_together': "(('type', 'campaign'),)", 'object_name': 'Phase'},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dpnk.Campaign']"}),
            'date_from': ('django.db.models.fields.DateField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'date_to': ('django.db.models.fields.DateField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'registration'", 'max_length': '16'})
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
            'address_recipient': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'address_street': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50'}),
            'address_street_number': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '10'}),
            'city': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dpnk.City']"}),
            'company': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'subsidiaries'", 'to': u"orm['dpnk.Company']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'dpnk.team': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('name', 'campaign'),)", 'object_name': 'Team'},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dpnk.Campaign']"}),
            'coordinator_campaign': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'coordinated_team'", 'unique': 'True', 'null': 'True', 'to': u"orm['dpnk.UserAttendance']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invitation_token': ('django.db.models.fields.CharField', [], {'default': "''", 'unique': 'True', 'max_length': '100'}),
            'member_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'subsidiary': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'teams'", 'to': u"orm['dpnk.Subsidiary']"})
        },
        u'dpnk.transaction': {
            'Meta': {'object_name': 'Transaction'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'transakce_create'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '500', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'polymorphic_ctype': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'polymorphic_dpnk.transaction_set'", 'null': 'True', 'to': u"orm['contenttypes.ContentType']"}),
            'realized': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'max_length': '50'}),
            'updated_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'transakce_update'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'user_attendance': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'transactions'", 'null': 'True', 'to': u"orm['dpnk.UserAttendance']"})
        },
        u'dpnk.trip': {
            'Meta': {'unique_together': "(('user_attendance', 'date'),)", 'object_name': 'Trip'},
            'date': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime.now'}),
            'distance_from': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'distance_to': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'trip_from': ('django.db.models.fields.BooleanField', [], {}),
            'trip_to': ('django.db.models.fields.BooleanField', [], {}),
            'user_attendance': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'user_trips'", 'null': 'True', 'blank': 'True', 'to': u"orm['dpnk.UserAttendance']"})
        },
        u'dpnk.tshirtsize': {
            'Meta': {'ordering': "['order']", 'unique_together': "(('name', 'campaign'),)", 'object_name': 'TShirtSize'},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dpnk.Campaign']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        },
        u'dpnk.useractiontransaction': {
            'Meta': {'object_name': 'UserActionTransaction', '_ormbases': [u'dpnk.Transaction']},
            u'transaction_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['dpnk.Transaction']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'dpnk.userattendance': {
            'Meta': {'unique_together': "(('userprofile', 'campaign'),)", 'object_name': 'UserAttendance'},
            'approved_for_team': ('django.db.models.fields.CharField', [], {'default': "'undecided'", 'max_length': '16'}),
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dpnk.Campaign']"}),
            'distance': ('django.db.models.fields.PositiveIntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            't_shirt_size': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dpnk.TShirtSize']", 'null': 'True'}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'users'", 'null': 'True', 'blank': 'True', 'to': u"orm['dpnk.Team']"}),
            'userprofile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dpnk.UserProfile']"})
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