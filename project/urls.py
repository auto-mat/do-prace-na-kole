from django.conf.urls import patterns, include, url
from django.contrib.gis import admin
admin.site.index_template = 'admin/my_custom_index.html'
admin.autodiscover()
from dpnk.views import questionnaire_results, questionnaire_answers, questions, answers
from dpnk import views
from django.conf.urls.static import static

from django.conf import settings

urlpatterns = patterns('',
    url(r'^admin/odpovedi/$',
        answers,
        name='admin_answers'),
    url(r'^admin/otazky/$',
        questions,
        name='admin_questions'),
    url(r'^admin/dotaznik_odpovedi/(?P<competition_slug>[0-9A-Za-z_\-]+)$',
        questionnaire_answers,
        name='admin_questionnaire_answers'),
    url(r'^admin/dotaznik/(?P<competition_slug>[0-9A-Za-z_\-]+)/$',
        questionnaire_results,
        name='admin_questionnaire_results'),
    url(r'^admin/losovani/(?P<competition_slug>[0-9A-Za-z_\-]+)/$',
        views.DrawResultsView.as_view(),
        name="admin_draw_results",
        ),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^chaining/', include('smart_selects.urls')),
    url(r'^admin/', include("massadmin.urls")),
    url(r'^', include("dpnk.urls")),
    url(r"^su/", include("django_su.urls")),
    url(r'^localeurl/', include('localeurl.urls')),
    url(r'^oauth2/', include('provider.oauth2.urls', namespace = 'oauth2')),
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if 'rosetta' in settings.INSTALLED_APPS:
    urlpatterns += patterns('',
            url(r'^rosetta/', include('rosetta.urls')),
                )

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += patterns('',
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )
