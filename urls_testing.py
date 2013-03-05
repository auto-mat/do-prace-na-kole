from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from dpnk.views import RegistrationFormDPNK, AutoRegistrationFormDPNK
from registration.views import register

urlpatterns = patterns('',
                       url(r'^admin/admin/', include(admin.site.urls)),
                       url(r'^registrace/registrace/$', 'dpnk.views.register',
                           {'success_url': '/registrace/platba/'}),
                       url(r'^registrace/registrace/(?P<token>[0-9A-Za-z]+)/(?P<initial_email>[^&]+)$$', 'dpnk.views.register',
                           {'success_url': '/registrace/platba/'}),
                       url(r'^registrace/pozvanky/$', 'dpnk.views.invite',
                           {'success_url': '/registrace/platba/'}),
                       url(r'^registrace/auto_registrace/$', 'dpnk.views.auto_register',
                           {'success_url': '/mesto/praha/'}),
                       #url(r'^registrace_tymu/$', 'dpnk.views.register_team'),
                       url(r'^registrace/login/$', 'django.contrib.auth.views.login'),
                       url(r'^registrace/zmena_hesla/$', 'django.contrib.auth.views.password_change'),
                       url(r'^registrace/zmena_hesla_hotovo/$', 'django.contrib.auth.views.password_change_done'),
                       url(r'^registrace/profil/$', 'dpnk.views.profile'),
                       url(r'^registrace/team_admin/$', 'dpnk.views.team_admin',
                           {'success_url': '/registrace/profil/'}),
                       url(r'^registrace/pridat_do_tymu/(?P<username>[^&]+)/$$', 'dpnk.views.approve_team_membership',
                           {'success_url': '/registrace/profil/'}),
                       url(r'^registrace/vysledky/$', 'dpnk.views.results',
                           {'template': 'registration/results.html'}),
                       url(r'^registrace/kratke_vysledky/$', 'dpnk.views.results',
                           {'template': 'registration/results_short.html'}),
                       url(r'^registrace/otazka/$', 'dpnk.views.questionaire'),
                       url(r'^registrace/cyklozamestnavatel_roku/$', 'dpnk.views.questionaire',
                           {'template': 'registration/company_survey.html'}),
                       url(r'^registrace/upravit_profil/$', 'dpnk.views.update_profile'),
                       url(r'^registrace/logout/$', 'django.contrib.auth.views.logout'),
                       url(r'^registrace/platba/$', 'dpnk.views.payment'),
                       url(r'^registrace/platba_uspesna/$', 'dpnk.views.payment_result',
                           {'success': True}),
                       url(r'^registrace/platba_neuspesna/$', 'dpnk.views.payment_result',
                           {'success': False}),
                       url(r'^registrace/platba_status$', 'dpnk.views.payment_status'),
                       url(r'^registrace/zapomenute_heslo/$', 'django.contrib.auth.views.password_reset'),
                       url(r'^registrace/zapomenute_heslo/odeslano/$', 'django.contrib.auth.views.password_reset_done'),
                       url(r'^registrace/zapomenute_heslo/zmena/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$$', 'django.contrib.auth.views.password_reset_confirm'),
                       url(r'^registrace/zapomenute_heslo/dokonceno/$', 'django.contrib.auth.views.password_reset_complete'),
                       url(r'^registrace/otazky/$', 'dpnk.views.questions'),
                       url(r'^registrace/cyklozamestnavatel_firmy/$', 'dpnk.views.company_survey'),
                       url(r'^registrace/cyklozamestnavatel_odpovedi/$', 'dpnk.views.company_survey_answers'),
                       url(r'^registrace/odpovedi/$', 'dpnk.views.answers'),
                       url(r'^registrace/chaining/', include('smart_selects.urls')),
                       )

