from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin
admin.autodiscover()
from dpnk.views import company_survey, company_survey_answers

from django.conf import settings

urlpatterns = patterns('',
    url(r'^admin/cyklozamestnavatel_odpovedi/$',
        company_survey_answers),
    url(r'^admin/cyklozamestnavatel_firmy/$',
        company_survey),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^chaining/', include('smart_selects.urls')),
    url(r'^dpnk/', include("dpnk.urls")),
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
