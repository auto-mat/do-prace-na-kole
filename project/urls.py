from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin
admin.autodiscover()
from dpnk.views import questionnaire_results, questionnaire_answers, draw_results, questions, answers

from django.conf import settings

urlpatterns = patterns('',
    url(r'^admin/odpovedi/$',
        answers),
    url(r'^admin/otazky/$',
        questions),
    url(r'^admin/dotaznik_odpovedi/(?P<competition_slug>[0-9A-Za-z_\-]+)$',
        questionnaire_answers),
    url(r'^admin/dotaznik/(?P<competition_slug>[0-9A-Za-z_\-]+)/$',
        questionnaire_results),
    url(r'^admin/losovani/(?P<competition_slug>[0-9A-Za-z_\-]+)/$',
        draw_results),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^chaining/', include('smart_selects.urls')),
    url(r'^dpnk/', include("dpnk.urls")),
    url(r"^su/", include("django_su.urls")),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^static/uploads/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
        }), 
        url(r'^static/static/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.STATIC_ROOT,
        }), 
    ) 
