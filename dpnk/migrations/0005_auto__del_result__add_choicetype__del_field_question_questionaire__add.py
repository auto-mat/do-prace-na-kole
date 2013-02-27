# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'Result'
        db.delete_table('dpnk_result')

        # Adding model 'ChoiceType'
        db.create_table('dpnk_choicetype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('competition', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dpnk.Competition'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('universal', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('dpnk', ['ChoiceType'])

        # Deleting field 'Question.questionaire'
        db.delete_column('dpnk_question', 'questionaire')

        # Adding field 'Question.choice_type'
        db.add_column('dpnk_question', 'choice_type',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=0, to=orm['dpnk.ChoiceType']),
                      keep_default=False)


        # Changing field 'Question.competition'
        db.alter_column('dpnk_question', 'competition_id', self.gf('django.db.models.fields.related.ForeignKey')(default=0, to=orm['dpnk.Competition']))
        # Adding field 'Payment.company_wants_to_pay'
        db.add_column('dpnk_payment', 'company_wants_to_pay',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Deleting field 'City.recent_event'
        db.delete_column('dpnk_city', 'recent_event')

        # Adding field 'City.admission_fee'
        db.add_column('dpnk_city', 'admission_fee',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=160),
                      keep_default=False)

        # Adding field 'Competition.without_admission'
        db.add_column('dpnk_competition', 'without_admission',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding M2M table for field company_competitors on 'Competition'
        db.create_table('dpnk_competition_company_competitors', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('competition', models.ForeignKey(orm['dpnk.competition'], null=False)),
            ('company', models.ForeignKey(orm['dpnk.company'], null=False))
        ))
        db.create_unique('dpnk_competition_company_competitors', ['competition_id', 'company_id'])

        # Deleting field 'UserProfile.wants_to_be_paid'
        db.delete_column('dpnk_userprofile', 'wants_to_be_paid')

        # Deleting field 'UserProfile.company_pays'
        db.delete_column('dpnk_userprofile', 'company_pays')

        # Adding field 'UserProfile.company_admin_unapproved'
        db.add_column('dpnk_userprofile', 'company_admin_unapproved',
                      self.gf('django.db.models.fields.BooleanField')(default=True),
                      keep_default=False)

        # Adding field 'UserProfile.t_shirt_size'
        db.add_column('dpnk_userprofile', 't_shirt_size',
                      self.gf('django.db.models.fields.CharField')(default='L', max_length=16),
                      keep_default=False)


        # Changing field 'UserProfile.user'
        db.alter_column('dpnk_userprofile', 'user_id', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True))
        # Deleting field 'Answer.result'
        db.delete_column('dpnk_answer', 'result_id')

        # Adding field 'Answer.team'
        db.add_column('dpnk_answer', 'team',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dpnk.Team'], null=True),
                      keep_default=False)

        # Adding field 'Answer.company'
        db.add_column('dpnk_answer', 'company',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dpnk.Company'], null=True),
                      keep_default=False)

        # Deleting field 'Subsidiary.name'
        db.delete_column('dpnk_subsidiary', 'name')

        # Deleting field 'Subsidiary.address'
        db.delete_column('dpnk_subsidiary', 'address')

        # Adding field 'Subsidiary.street'
        db.add_column('dpnk_subsidiary', 'street',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=50),
                      keep_default=False)

        # Adding field 'Subsidiary.street_number'
        db.add_column('dpnk_subsidiary', 'street_number',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=10),
                      keep_default=False)

        # Adding field 'Subsidiary.recipient'
        db.add_column('dpnk_subsidiary', 'recipient',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=50),
                      keep_default=False)

        # Adding field 'Subsidiary.district'
        db.add_column('dpnk_subsidiary', 'district',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=50),
                      keep_default=False)

        # Adding field 'Subsidiary.PSC'
        db.add_column('dpnk_subsidiary', 'PSC',
                      self.gf('django.db.models.fields.IntegerField')(default=0),
                      keep_default=False)

        # Adding field 'Choice.choice_type'
        db.add_column('dpnk_choice', 'choice_type',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=0, to=orm['dpnk.ChoiceType']),
                      keep_default=False)


    def backwards(self, orm):
        # Adding model 'Result'
        db.create_table('dpnk_result', (
            ('distance', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dpnk.UserProfile'], null=True, blank=True)),
            ('team', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dpnk.Team'], null=True, blank=True)),
            ('company', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dpnk.Company'], null=True, blank=True)),
            ('trips_count', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('points', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('competition', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dpnk.Competition'])),
            ('order', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('dpnk', ['Result'])

        # Deleting model 'ChoiceType'
        db.delete_table('dpnk_choicetype')

        # Adding field 'Question.questionaire'
        db.add_column('dpnk_question', 'questionaire',
                      self.gf('django.db.models.fields.CharField')(default=1, max_length=16),
                      keep_default=False)

        # Deleting field 'Question.choice_type'
        db.delete_column('dpnk_question', 'choice_type_id')


        # Changing field 'Question.competition'
        db.alter_column('dpnk_question', 'competition_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dpnk.Competition'], null=True))
        # Deleting field 'Payment.company_wants_to_pay'
        db.delete_column('dpnk_payment', 'company_wants_to_pay')

        # Adding field 'City.recent_event'
        db.add_column('dpnk_city', 'recent_event',
                      self.gf('django.db.models.fields.TextField')(null=True, blank=True),
                      keep_default=False)

        # Deleting field 'City.admission_fee'
        db.delete_column('dpnk_city', 'admission_fee')

        # Deleting field 'Competition.without_admission'
        db.delete_column('dpnk_competition', 'without_admission')

        # Removing M2M table for field company_competitors on 'Competition'
        db.delete_table('dpnk_competition_company_competitors')

        # Adding field 'UserProfile.wants_to_be_paid'
        db.add_column('dpnk_userprofile', 'wants_to_be_paid',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'UserProfile.company_pays'
        db.add_column('dpnk_userprofile', 'company_pays',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Deleting field 'UserProfile.company_admin_unapproved'
        db.delete_column('dpnk_userprofile', 'company_admin_unapproved')

        # Deleting field 'UserProfile.t_shirt_size'
        db.delete_column('dpnk_userprofile', 't_shirt_size')


        # Changing field 'UserProfile.user'
        db.alter_column('dpnk_userprofile', 'user_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], unique=True))
        # Adding field 'Answer.result'
        db.add_column('dpnk_answer', 'result',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dpnk.Result'], null=True),
                      keep_default=False)

        # Deleting field 'Answer.team'
        db.delete_column('dpnk_answer', 'team_id')

        # Deleting field 'Answer.company'
        db.delete_column('dpnk_answer', 'company_id')

        # Adding field 'Subsidiary.name'
        db.add_column('dpnk_subsidiary', 'name',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=60),
                      keep_default=False)

        # Adding field 'Subsidiary.address'
        db.add_column('dpnk_subsidiary', 'address',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=50),
                      keep_default=False)

        # Deleting field 'Subsidiary.street'
        db.delete_column('dpnk_subsidiary', 'street')

        # Deleting field 'Subsidiary.street_number'
        db.delete_column('dpnk_subsidiary', 'street_number')

        # Deleting field 'Subsidiary.recipient'
        db.delete_column('dpnk_subsidiary', 'recipient')

        # Deleting field 'Subsidiary.district'
        db.delete_column('dpnk_subsidiary', 'district')

        # Deleting field 'Subsidiary.PSC'
        db.delete_column('dpnk_subsidiary', 'PSC')

        # Deleting field 'Choice.choice_type'
        db.delete_column('dpnk_choice', 'choice_type_id')


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
            'choice_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dpnk.ChoiceType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'points': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dpnk.Question']"}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '300'})
        },
        'dpnk.choicetype': {
            'Meta': {'object_name': 'ChoiceType'},
            'competition': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dpnk.Competition']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'universal': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'dpnk.city': {
            'Meta': {'object_name': 'City'},
            'admission_fee': ('django.db.models.fields.PositiveIntegerField', [], {'default': '160'}),
            'city_admins': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'administrated_cities'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['dpnk.UserProfile']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '40'})
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
            'company_competitors': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'competitions'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['dpnk.Company']"}),
            'competitor_type': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
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
            'PSC': ('django.db.models.fields.IntegerField', [], {}),
            'city': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dpnk.City']"}),
            'company': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dpnk.Company']"}),
            'district': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'recipient': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'street': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'street_number': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'dpnk.team': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Team'},
            'coordinator': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'coordinated_team'", 'unique': 'True', 'null': 'True', 'to': "orm['dpnk.UserProfile']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'subsidiary': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dpnk.Subsidiary']"})
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
            'company_admin_unapproved': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'distance': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'firstname': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'libero': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'surname': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            't_shirt_size': ('django.db.models.fields.CharField', [], {'default': "'L'", 'max_length': '16'}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dpnk.Team']"}),
            'telephone': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'trips': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'dpnk.voucher': {
            'Meta': {'object_name': 'Voucher'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dpnk.UserProfile']", 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['dpnk']
