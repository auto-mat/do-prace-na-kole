from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from dpnk.views import RegistrationFormDPNK, AutoRegistrationFormDPNK
from registration.views import register

urlpatterns = patterns('',
                       url(r'^admin/', include(admin.site.urls)),
                       url(r'^registrace/$', 'dpnk.views.register',
                           {'success_url': '/registrace/platba/'}),
                       url(r'^registrace/(?P<token>[0-9A-Za-z]+)/(?P<initial_email>[^&]+)$$', 'dpnk.views.register',
                           {'success_url': '/registrace/platba/'}),
                       url(r'^pozvanky/$', 'dpnk.views.invite',
                           {'success_url': '/registrace/platba/'}),
                       url(r'^auto_registrace/$', 'dpnk.views.auto_register',
                           {'success_url': '/mesto/praha/'}),
                       url(r'^registrace_tymu/$', 'dpnk.views.register_team'),
                       url(r'^login/$', 'django.contrib.auth.views.login'),
                       url(r'^zmena_hesla/$', 'django.contrib.auth.views.password_change'),
                       url(r'^zmena_hesla_hotovo/$', 'django.contrib.auth.views.password_change_done'),
                       url(r'^profil/$', 'dpnk.views.profile'),
                       url(r'^team_admin/$', 'dpnk.views.team_admin',
                           {'success_url': '/registrace/profil/'}),
                       url(r'^pridat_do_tymu/(?P<username>[^&]+)/$$', 'dpnk.views.approve_team_membership',
                           {'success_url': '/registrace/profil/'}),
                       url(r'^vysledky/$', 'dpnk.views.results',
                           {'template': 'registration/results.html'}),
                       url(r'^kratke_vysledky/$', 'dpnk.views.results',
                           {'template': 'registration/results_short.html'}),
                       url(r'^otazka/$', 'dpnk.views.questionaire'),
                       url(r'^cyklozamestnavatel_roku/$', 'dpnk.views.questionaire',
                           {'template': 'registration/company_survey.html'}),
                       url(r'^upravit_profil/$', 'dpnk.views.update_profile'),
                       url(r'^logout/$', 'django.contrib.auth.views.logout'),
                       url(r'^platba/$', 'dpnk.views.payment'),
                       url(r'^platba_uspesna/$', 'dpnk.views.payment_result',
                           {'success': True}),
                       url(r'^platba_neuspesna/$', 'dpnk.views.payment_result',
                           {'success': False}),
                       url(r'^platba_status$', 'dpnk.views.payment_status'),
                       url(r'^zapomenute_heslo/$', 'django.contrib.auth.views.password_reset'),
                       url(r'^zapomenute_heslo/odeslano/$', 'django.contrib.auth.views.password_reset_done'),
                       url(r'^zapomenute_heslo/zmena/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$$', 'django.contrib.auth.views.password_reset_confirm'),
                       url(r'^zapomenute_heslo/dokonceno/$', 'django.contrib.auth.views.password_reset_complete'),
                       url(r'^otazky/$', 'dpnk.views.questions'),
                       url(r'^cyklozamestnavatel_firmy/$', 'dpnk.views.company_survey'),
                       url(r'^cyklozamestnavatel_odpovedi/$', 'dpnk.views.company_survey_answers'),
                       url(r'^odpovedi/$', 'dpnk.views.answers'),
                       url(r'^chaining/', include('smart_selects.urls')),
                       )

