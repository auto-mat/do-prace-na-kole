from ajax_select import urls as ajax_select_urls

from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib.gis import admin
from django.http import HttpResponse

from dpnk import views
from dpnk.rest import router
from dpnk.views import answers, questionnaire_answers, questionnaire_results, questions

admin.site.index_template = 'admin/my_custom_index.html'
admin.autodiscover()

urlpatterns = [
    url(
        r'^admin/odpovedi/$',
        answers,
        name='admin_answers',
    ),
    url(
        r'^admin/otazky/$',
        questions,
        name='admin_questions',
    ),
    url(
        r'^admin/dotaznik_odpovedi/(?P<competition_slug>[0-9A-Za-z_\-]+)$',
        questionnaire_answers,
        name='admin_questionnaire_answers',
    ),
    url(
        r'^admin/dotaznik/(?P<competition_slug>[0-9A-Za-z_\-]+)/$',
        questionnaire_results,
        name='admin_questionnaire_results',
    ),
    url(
        r'^admin/losovani/(?P<competition_slug>[0-9A-Za-z_\-]+)/$',
        views.DrawResultsView.as_view(),
        name="admin_draw_results",
    ),
    url(r'^admin/', admin.site.urls),
    url(r'^chaining/', include('smart_selects.urls')),
    url(r'^adminactions/', include('adminactions.urls')),
    url(r"^su/", include("django_su.urls")),
    url(r'^ajax_select/', include(ajax_select_urls)),
    url(r'^oauth2/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    url(r'^redactor/', include('redactor.urls')),
    url(r'^rest/', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^', include("dpnk.urls")),
    url(r'^coupons/', include("coupons.urls")),
    url(r'^t_shirt/', include("t_shirt_delivery.urls")),
    url(r'^robots.txt$', lambda r: HttpResponse("User-agent: *\nAllow:", content_type="text/plain")),
    url(r'^', include('favicon.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += i18n_patterns(
    url(r'^', include("dpnk.urls")),
    url(r'^', include("t_shirt_delivery.urls")),
    url(r'^', include("coupons.urls")),
)

if 'rosetta' in settings.INSTALLED_APPS:
    urlpatterns += [
        url(r'^rosetta/', include('rosetta.urls')),
    ]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
