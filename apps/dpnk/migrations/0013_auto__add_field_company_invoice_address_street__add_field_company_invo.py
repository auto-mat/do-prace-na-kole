# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Company.invoice_address_street'
        db.add_column('dpnk_company', 'invoice_address_street',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=50),
                      keep_default=False)

        # Adding field 'Company.invoice_address_street_number'
        db.add_column('dpnk_company', 'invoice_address_street_number',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=10),
                      keep_default=False)

        # Adding field 'Company.invoice_address_recipient'
        db.add_column('dpnk_company', 'invoice_address_recipient',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=50),
                      keep_default=False)

        # Adding field 'Company.invoice_address_district'
        db.add_column('dpnk_company', 'invoice_address_district',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=50),
                      keep_default=False)

        # Adding field 'Company.invoice_address_psc'
        db.add_column('dpnk_company', 'invoice_address_psc',
                      self.gf('django.db.models.fields.IntegerField')(default=0),
                      keep_default=False)

        # Adding field 'Company.invoice_address_city'
        db.add_column('dpnk_company', 'invoice_address_city',
                      self.gf('django.db.models.fields.CharField')(default=0, max_length=50),
                      keep_default=False)

        # Adding field 'Company.ico'
        db.add_column('dpnk_company', 'ico',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)

        # Deleting field 'UserProfile.gender'
        db.delete_column('dpnk_userprofile', 'gender')

        # Deleting field 'UserProfile.libero'
        db.delete_column('dpnk_userprofile', 'libero')

        # Adding field 'UserProfile.motivation_company_admin'
        db.add_column('dpnk_userprofile', 'motivation_company_admin',
                      self.gf('django.db.models.fields.TextField')(default='', max_length=5000),
                      keep_default=False)


        # Changing field 'UserProfile.approved_for_team'
        db.alter_column('dpnk_userprofile', 'approved_for_team', self.gf('django.db.models.fields.CharField')(max_length=16))
        # Adding field 'Subsidiary.address_city'
        db.add_column('dpnk_subsidiary', 'address_city',
                      self.gf('django.db.models.fields.CharField')(default=0, max_length=50),
                      keep_default=False)


        # Changing field 'Team.coordinator'
        db.alter_column('dpnk_team', 'coordinator_id', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, null=True, to=orm['dpnk.UserProfile']))

    def backwards(self, orm):
        # Deleting field 'Company.invoice_address_street'
        db.delete_column('dpnk_company', 'invoice_address_street')

        # Deleting field 'Company.invoice_address_street_number'
        db.delete_column('dpnk_company', 'invoice_address_street_number')

        # Deleting field 'Company.invoice_address_recipient'
        db.delete_column('dpnk_company', 'invoice_address_recipient')

        # Deleting field 'Company.invoice_address_district'
        db.delete_column('dpnk_company', 'invoice_address_district')

        # Deleting field 'Company.invoice_address_psc'
        db.delete_column('dpnk_company', 'invoice_address_psc')

        # Deleting field 'Company.invoice_address_city'
        db.delete_column('dpnk_company', 'invoice_address_city')

        # Deleting field 'Company.ico'
        db.delete_column('dpnk_company', 'ico')

        # Adding field 'UserProfile.gender'
        db.add_column('dpnk_userprofile', 'gender',
                      self.gf('django.db.models.fields.CharField')(default='man', max_length=16),
                      keep_default=False)

        # Adding field 'UserProfile.libero'
        db.add_column('dpnk_userprofile', 'libero',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Deleting field 'UserProfile.motivation_company_admin'
        db.delete_column('dpnk_userprofile', 'motivation_company_admin')


        # Changing field 'UserProfile.approved_for_team'
        db.alter_column('dpnk_userprofile', 'approved_for_team', self.gf('django.db.models.fields.BooleanField')())
        # Deleting field 'Subsidiary.address_city'
        db.delete_column('dpnk_subsidiary', 'address_city')


        # Changing field 'Team.coordinator'
        db.alter_column('dpnk_team', 'coordinator_id', self.gf('django.db.models.fields.related.OneToOneField')(default=None, unique=True, to=orm['dpnk.UserProfile']))

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
            'company': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dpnk.Company']", 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'points_given': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dpnk.Question']"}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dpnk.Team']", 'null': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dpnk.UserProfile']", 'null': 'True'})
        },
        'dpnk.choice': {
            'Meta': {'object_name': 'Choice'},
            'choice_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'choices'", 'to': "orm['dpnk.ChoiceType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'points': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '300'})
        },
        'dpnk.choicetype': {
            'Meta': {'unique_together': "(('competition', 'name'),)", 'object_name': 'ChoiceType'},
            'competition': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dpnk.Competition']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '40', 'unique': 'True', 'null': 'True'}),
            'universal': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'dpnk.city': {
            'Meta': {'object_name': 'City'},
            'admission_fee': ('django.db.models.fields.PositiveIntegerField', [], {'default': '160'}),
            'city_admins': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'administrated_cities'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['dpnk.UserProfile']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40'})
        },
        'dpnk.company': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Company'},
            'company_admin': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'administrated_company'", 'unique': 'True', 'null': 'True', 'to': "orm['dpnk.UserProfile']"}),
            'ico': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invoice_address_city': ('django.db.models.fields.CharField', [], {'default': '0', 'max_length': '50'}),
            'invoice_address_district': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50'}),
            'invoice_address_psc': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'invoice_address_recipient': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50'}),
            'invoice_address_street': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50'}),
            'invoice_address_street_number': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '10'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60'})
        },
        'dpnk.competition': {
            'Meta': {'object_name': 'Competition'},
            'city': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dpnk.City']", 'null': 'True', 'blank': 'True'}),
            'company': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dpnk.Company']", 'null': 'True', 'blank': 'True'}),
            'company_competitors': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'competitions'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['dpnk.Company']"}),
            'competitor_type': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40'}),
            'team_competitors': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'competitions'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['dpnk.Team']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'user_competitors': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'competitions'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['dpnk.UserProfile']"}),
            'without_admission': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'dpnk.payment': {
            'Meta': {'object_name': 'Payment'},
            'amount': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'company_wants_to_pay': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
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
            'choice_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dpnk.ChoiceType']"}),
            'competition': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dpnk.Competition']"}),
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {'max_length': '500'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'with_attachment': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'with_comment': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        'dpnk.subsidiary': {
            'Meta': {'object_name': 'Subsidiary'},
            'address_city': ('django.db.models.fields.CharField', [], {'default': '0', 'max_length': '50'}),
            'address_district': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50'}),
            'address_psc': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'address_recipient': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50'}),
            'address_street': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50'}),
            'address_street_number': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '10'}),
            'city': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dpnk.City']"}),
            'company': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'subsidiaries'", 'to': "orm['dpnk.Company']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'dpnk.team': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Team'},
            'coordinator': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'coordinated_team'", 'unique': 'True', 'null': 'True', 'to': "orm['dpnk.UserProfile']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invitation_token': ('django.db.models.fields.CharField', [], {'default': "'3F0WJDJAF2Q0TT99DCRAVOZ19J2TQO'", 'unique': 'True', 'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'subsidiary': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'teams'", 'to': "orm['dpnk.Subsidiary']"})
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
            'approved_for_team': ('django.db.models.fields.CharField', [], {'default': "'undecided'", 'max_length': '16'}),
            'company_admin_unapproved': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'distance': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'firstname': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'motivation_company_admin': ('django.db.models.fields.TextField', [], {'default': "''", 'max_length': '5000'}),
            'surname': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            't_shirt_size': ('django.db.models.fields.CharField', [], {'default': "'L'", 'max_length': '16'}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dpnk.Team']"}),
            'telephone': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'trips': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'userprofile'", 'unique': 'True', 'to': "orm['auth.User']"})
        },
        'dpnk.voucher': {
            'Meta': {'object_name': 'Voucher'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dpnk.UserProfile']", 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['dpnk']