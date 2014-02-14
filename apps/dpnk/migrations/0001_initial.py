# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'City'
        db.create_table(u'dpnk_city', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=40)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50)),
            ('admission_fee', self.gf('django.db.models.fields.PositiveIntegerField')(default=160)),
        ))
        db.send_create_signal(u'dpnk', ['City'])

        # Adding M2M table for field city_admins on 'City'
        db.create_table(u'dpnk_city_city_admins', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('city', models.ForeignKey(orm[u'dpnk.city'], null=False)),
            ('userprofile', models.ForeignKey(orm[u'dpnk.userprofile'], null=False))
        ))
        db.create_unique(u'dpnk_city_city_admins', ['city_id', 'userprofile_id'])

        # Adding model 'Company'
        db.create_table(u'dpnk_company', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=60)),
            ('address_street', self.gf('django.db.models.fields.CharField')(default='', max_length=50)),
            ('address_street_number', self.gf('django.db.models.fields.CharField')(default='', max_length=10)),
            ('address_recipient', self.gf('django.db.models.fields.CharField')(default='', max_length=50)),
            ('address_district', self.gf('django.db.models.fields.CharField')(default='', max_length=50, null=True, blank=True)),
            ('address_psc', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('address_city', self.gf('django.db.models.fields.CharField')(default='', max_length=50)),
            ('ico', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
        ))
        db.send_create_signal(u'dpnk', ['Company'])

        # Adding model 'Subsidiary'
        db.create_table(u'dpnk_subsidiary', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('address_street', self.gf('django.db.models.fields.CharField')(default='', max_length=50)),
            ('address_street_number', self.gf('django.db.models.fields.CharField')(default='', max_length=10)),
            ('address_recipient', self.gf('django.db.models.fields.CharField')(default='', max_length=50)),
            ('address_district', self.gf('django.db.models.fields.CharField')(default='', max_length=50, null=True, blank=True)),
            ('address_psc', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('address_city', self.gf('django.db.models.fields.CharField')(default='', max_length=50)),
            ('company', self.gf('django.db.models.fields.related.ForeignKey')(related_name='subsidiaries', to=orm['dpnk.Company'])),
            ('city', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dpnk.City'])),
        ))
        db.send_create_signal(u'dpnk', ['Subsidiary'])

        # Adding model 'Team'
        db.create_table(u'dpnk_team', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50)),
            ('subsidiary', self.gf('django.db.models.fields.related.ForeignKey')(related_name='teams', to=orm['dpnk.Subsidiary'])),
            ('coordinator', self.gf('django.db.models.fields.related.OneToOneField')(blank=True, related_name='coordinated_team', unique=True, null=True, to=orm['dpnk.UserProfile'])),
            ('invitation_token', self.gf('django.db.models.fields.CharField')(default='', unique=True, max_length=100)),
            ('member_count', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal(u'dpnk', ['Team'])

        # Adding model 'UserProfile'
        db.create_table(u'dpnk_userprofile', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(related_name='userprofile', unique=True, to=orm['auth.User'])),
            ('distance', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('telephone', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('team', self.gf('django.db.models.fields.related.ForeignKey')(related_name='users', to=orm['dpnk.Team'])),
            ('approved_for_team', self.gf('django.db.models.fields.CharField')(default='undecided', max_length=16)),
            ('language', self.gf('django.db.models.fields.CharField')(default='cs', max_length=16)),
            ('t_shirt_size', self.gf('django.db.models.fields.CharField')(default='mL', max_length=16)),
            ('mailing_id', self.gf('django.db.models.fields.CharField')(default=None, max_length=128, null=True, db_index=True, blank=True)),
        ))
        db.send_create_signal(u'dpnk', ['UserProfile'])

        # Adding model 'CompanyAdmin'
        db.create_table(u'dpnk_companyadmin', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(related_name='company_admin', unique=True, to=orm['auth.User'])),
            ('company_admin_approved', self.gf('django.db.models.fields.CharField')(default='undecided', max_length=16)),
            ('motivation_company_admin', self.gf('django.db.models.fields.TextField')(default='', max_length=5000, null=True, blank=True)),
            ('telephone', self.gf('django.db.models.fields.CharField')(max_length=30, null=True, blank=True)),
            ('administrated_company', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='company_admin', unique=True, null=True, to=orm['dpnk.Company'])),
            ('mailing_id', self.gf('django.db.models.fields.TextField')(default='', null=True, blank=True)),
        ))
        db.send_create_signal(u'dpnk', ['CompanyAdmin'])

        # Adding model 'Payment'
        db.create_table(u'dpnk_payment', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='payments', null=True, blank=True, to=orm['dpnk.UserProfile'])),
            ('order_id', self.gf('django.db.models.fields.CharField')(default='', max_length=50, null=True, blank=True)),
            ('session_id', self.gf('django.db.models.fields.CharField')(default='', max_length=50, null=True, blank=True)),
            ('trans_id', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('amount', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('description', self.gf('django.db.models.fields.CharField')(default='', max_length=500, null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('realized', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('pay_type', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('status', self.gf('django.db.models.fields.PositiveIntegerField')(default=1, max_length=50, null=True, blank=True)),
            ('error', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'dpnk', ['Payment'])

        # Adding model 'Trip'
        db.create_table(u'dpnk_trip', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='user_trips', to=orm['dpnk.UserProfile'])),
            ('date', self.gf('django.db.models.fields.DateField')(default=datetime.datetime.now)),
            ('trip_to', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('trip_from', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('distance_to', self.gf('django.db.models.fields.IntegerField')(default=None, null=True, blank=True)),
            ('distance_from', self.gf('django.db.models.fields.IntegerField')(default=None, null=True, blank=True)),
        ))
        db.send_create_signal(u'dpnk', ['Trip'])

        # Adding unique constraint on 'Trip', fields ['user', 'date']
        db.create_unique(u'dpnk_trip', ['user_id', 'date'])

        # Adding model 'Competition'
        db.create_table(u'dpnk_competition', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=40)),
            ('slug', self.gf('django.db.models.fields.SlugField')(default='', unique=True, max_length=50)),
            ('url', self.gf('django.db.models.fields.URLField')(default='', max_length=200, null=True, blank=True)),
            ('date_from', self.gf('django.db.models.fields.DateField')(default=datetime.datetime(2013, 5, 1, 0, 0))),
            ('date_to', self.gf('django.db.models.fields.DateField')(default=datetime.datetime(2013, 5, 31, 0, 0))),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('competitor_type', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('city', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dpnk.City'], null=True, blank=True)),
            ('company', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dpnk.Company'], null=True, blank=True)),
            ('without_admission', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('is_public', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal(u'dpnk', ['Competition'])

        # Adding M2M table for field user_competitors on 'Competition'
        db.create_table(u'dpnk_competition_user_competitors', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('competition', models.ForeignKey(orm[u'dpnk.competition'], null=False)),
            ('userprofile', models.ForeignKey(orm[u'dpnk.userprofile'], null=False))
        ))
        db.create_unique(u'dpnk_competition_user_competitors', ['competition_id', 'userprofile_id'])

        # Adding M2M table for field team_competitors on 'Competition'
        db.create_table(u'dpnk_competition_team_competitors', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('competition', models.ForeignKey(orm[u'dpnk.competition'], null=False)),
            ('team', models.ForeignKey(orm[u'dpnk.team'], null=False))
        ))
        db.create_unique(u'dpnk_competition_team_competitors', ['competition_id', 'team_id'])

        # Adding M2M table for field company_competitors on 'Competition'
        db.create_table(u'dpnk_competition_company_competitors', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('competition', models.ForeignKey(orm[u'dpnk.competition'], null=False)),
            ('company', models.ForeignKey(orm[u'dpnk.company'], null=False))
        ))
        db.create_unique(u'dpnk_competition_company_competitors', ['competition_id', 'company_id'])

        # Adding model 'CompetitionResult'
        db.create_table(u'dpnk_competitionresult', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('userprofile', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='competitions_results', null=True, blank=True, to=orm['dpnk.UserProfile'])),
            ('team', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='competitions_results', null=True, blank=True, to=orm['dpnk.Team'])),
            ('competition', self.gf('django.db.models.fields.related.ForeignKey')(related_name='results', to=orm['dpnk.Competition'])),
            ('result', self.gf('django.db.models.fields.FloatField')(default=None, null=True, blank=True)),
        ))
        db.send_create_signal(u'dpnk', ['CompetitionResult'])

        # Adding unique constraint on 'CompetitionResult', fields ['userprofile', 'competition']
        db.create_unique(u'dpnk_competitionresult', ['userprofile_id', 'competition_id'])

        # Adding unique constraint on 'CompetitionResult', fields ['team', 'competition']
        db.create_unique(u'dpnk_competitionresult', ['team_id', 'competition_id'])

        # Adding model 'ChoiceType'
        db.create_table(u'dpnk_choicetype', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('competition', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dpnk.Competition'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=40, unique=True, null=True)),
            ('universal', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'dpnk', ['ChoiceType'])

        # Adding unique constraint on 'ChoiceType', fields ['competition', 'name']
        db.create_unique(u'dpnk_choicetype', ['competition_id', 'name'])

        # Adding model 'Question'
        db.create_table(u'dpnk_question', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('text', self.gf('django.db.models.fields.TextField')(max_length=500)),
            ('date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('with_comment', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('with_attachment', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('order', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('competition', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dpnk.Competition'])),
            ('choice_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dpnk.ChoiceType'])),
        ))
        db.send_create_signal(u'dpnk', ['Question'])

        # Adding unique constraint on 'Question', fields ['competition', 'order']
        db.create_unique(u'dpnk_question', ['competition_id', 'order'])

        # Adding model 'Choice'
        db.create_table(u'dpnk_choice', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('choice_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='choices', to=orm['dpnk.ChoiceType'])),
            ('text', self.gf('django.db.models.fields.CharField')(max_length=250, db_index=True)),
            ('points', self.gf('django.db.models.fields.IntegerField')(default=None, null=True, blank=True)),
        ))
        db.send_create_signal(u'dpnk', ['Choice'])

        # Adding unique constraint on 'Choice', fields ['choice_type', 'text']
        db.create_unique(u'dpnk_choice', ['choice_type_id', 'text'])

        # Adding model 'Answer'
        db.create_table(u'dpnk_answer', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dpnk.UserProfile'], null=True, blank=True)),
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dpnk.Question'])),
            ('comment', self.gf('django.db.models.fields.TextField')(max_length=600, null=True, blank=True)),
            ('points_given', self.gf('django.db.models.fields.IntegerField')(default=None, null=True, blank=True)),
            ('attachment', self.gf('django.db.models.fields.files.FileField')(max_length=600)),
        ))
        db.send_create_signal(u'dpnk', ['Answer'])

        # Adding unique constraint on 'Answer', fields ['user', 'question']
        db.create_unique(u'dpnk_answer', ['user_id', 'question_id'])

        # Adding M2M table for field choices on 'Answer'
        db.create_table(u'dpnk_answer_choices', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('answer', models.ForeignKey(orm[u'dpnk.answer'], null=False)),
            ('choice', models.ForeignKey(orm[u'dpnk.choice'], null=False))
        ))
        db.create_unique(u'dpnk_answer_choices', ['answer_id', 'choice_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'Answer', fields ['user', 'question']
        db.delete_unique(u'dpnk_answer', ['user_id', 'question_id'])

        # Removing unique constraint on 'Choice', fields ['choice_type', 'text']
        db.delete_unique(u'dpnk_choice', ['choice_type_id', 'text'])

        # Removing unique constraint on 'Question', fields ['competition', 'order']
        db.delete_unique(u'dpnk_question', ['competition_id', 'order'])

        # Removing unique constraint on 'ChoiceType', fields ['competition', 'name']
        db.delete_unique(u'dpnk_choicetype', ['competition_id', 'name'])

        # Removing unique constraint on 'CompetitionResult', fields ['team', 'competition']
        db.delete_unique(u'dpnk_competitionresult', ['team_id', 'competition_id'])

        # Removing unique constraint on 'CompetitionResult', fields ['userprofile', 'competition']
        db.delete_unique(u'dpnk_competitionresult', ['userprofile_id', 'competition_id'])

        # Removing unique constraint on 'Trip', fields ['user', 'date']
        db.delete_unique(u'dpnk_trip', ['user_id', 'date'])

        # Deleting model 'City'
        db.delete_table(u'dpnk_city')

        # Removing M2M table for field city_admins on 'City'
        db.delete_table('dpnk_city_city_admins')

        # Deleting model 'Company'
        db.delete_table(u'dpnk_company')

        # Deleting model 'Subsidiary'
        db.delete_table(u'dpnk_subsidiary')

        # Deleting model 'Team'
        db.delete_table(u'dpnk_team')

        # Deleting model 'UserProfile'
        db.delete_table(u'dpnk_userprofile')

        # Deleting model 'CompanyAdmin'
        db.delete_table(u'dpnk_companyadmin')

        # Deleting model 'Payment'
        db.delete_table(u'dpnk_payment')

        # Deleting model 'Trip'
        db.delete_table(u'dpnk_trip')

        # Deleting model 'Competition'
        db.delete_table(u'dpnk_competition')

        # Removing M2M table for field user_competitors on 'Competition'
        db.delete_table('dpnk_competition_user_competitors')

        # Removing M2M table for field team_competitors on 'Competition'
        db.delete_table('dpnk_competition_team_competitors')

        # Removing M2M table for field company_competitors on 'Competition'
        db.delete_table('dpnk_competition_company_competitors')

        # Deleting model 'CompetitionResult'
        db.delete_table(u'dpnk_competitionresult')

        # Deleting model 'ChoiceType'
        db.delete_table(u'dpnk_choicetype')

        # Deleting model 'Question'
        db.delete_table(u'dpnk_question')

        # Deleting model 'Choice'
        db.delete_table(u'dpnk_choice')

        # Deleting model 'Answer'
        db.delete_table(u'dpnk_answer')

        # Removing M2M table for field choices on 'Answer'
        db.delete_table('dpnk_answer_choices')


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
            'Meta': {'ordering': "('user__team__subsidiary__city', 'pk')", 'unique_together': "(('user', 'question'),)", 'object_name': 'Answer'},
            'attachment': ('django.db.models.fields.files.FileField', [], {'max_length': '600'}),
            'choices': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['dpnk.Choice']", 'symmetrical': 'False'}),
            'comment': ('django.db.models.fields.TextField', [], {'max_length': '600', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'points_given': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dpnk.Question']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dpnk.UserProfile']", 'null': 'True', 'blank': 'True'})
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
            'city': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dpnk.City']", 'null': 'True', 'blank': 'True'}),
            'company': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dpnk.Company']", 'null': 'True', 'blank': 'True'}),
            'company_competitors': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'competitions'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['dpnk.Company']"}),
            'competitor_type': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'date_from': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime(2013, 5, 1, 0, 0)'}),
            'date_to': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime(2013, 5, 31, 0, 0)'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40'}),
            'slug': ('django.db.models.fields.SlugField', [], {'default': "''", 'unique': 'True', 'max_length': '50'}),
            'team_competitors': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'competitions'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['dpnk.Team']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'url': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'user_competitors': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'competitions'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['dpnk.UserProfile']"}),
            'without_admission': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'dpnk.competitionresult': {
            'Meta': {'unique_together': "(('userprofile', 'competition'), ('team', 'competition'))", 'object_name': 'CompetitionResult'},
            'competition': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'results'", 'to': u"orm['dpnk.Competition']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'result': ('django.db.models.fields.FloatField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'competitions_results'", 'null': 'True', 'blank': 'True', 'to': u"orm['dpnk.Team']"}),
            'userprofile': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'competitions_results'", 'null': 'True', 'blank': 'True', 'to': u"orm['dpnk.UserProfile']"})
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
            'user': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'payments'", 'null': 'True', 'blank': 'True', 'to': u"orm['dpnk.UserProfile']"})
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
            'coordinator': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'coordinated_team'", 'unique': 'True', 'null': 'True', 'to': u"orm['dpnk.UserProfile']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invitation_token': ('django.db.models.fields.CharField', [], {'default': "''", 'unique': 'True', 'max_length': '100'}),
            'member_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'subsidiary': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'teams'", 'to': u"orm['dpnk.Subsidiary']"})
        },
        u'dpnk.trip': {
            'Meta': {'unique_together': "(('user', 'date'),)", 'object_name': 'Trip'},
            'date': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime.now'}),
            'distance_from': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'distance_to': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'trip_from': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'trip_to': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'user_trips'", 'to': u"orm['dpnk.UserProfile']"})
        },
        u'dpnk.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'approved_for_team': ('django.db.models.fields.CharField', [], {'default': "'undecided'", 'max_length': '16'}),
            'distance': ('django.db.models.fields.PositiveIntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "'cs'", 'max_length': '16'}),
            'mailing_id': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '128', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            't_shirt_size': ('django.db.models.fields.CharField', [], {'default': "'mL'", 'max_length': '16'}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'users'", 'to': u"orm['dpnk.Team']"}),
            'telephone': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'userprofile'", 'unique': 'True', 'to': u"orm['auth.User']"})
        }
    }

    complete_apps = ['dpnk']