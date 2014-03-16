from django.conf.urls import patterns, include, url
from django.contrib import admin
admin.autodiscover()
from dpnk.views import questionnaire_results, questionnaire_answers, draw_results, questions, answers
from django.conf.urls.static import static

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
    url(r'^admin/', include("massadmin.urls")),
    url(r'^dpnk/', include("dpnk.urls")),
    url(r"^su/", include("django_su.urls")),
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
