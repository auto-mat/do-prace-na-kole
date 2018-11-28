from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib.gis import admin
from django.http import HttpResponse
from django.views.generic import RedirectView

from dpnk.rest import router

from rest_framework.documentation import include_docs_urls

admin.autodiscover()


class OldLanguageRedirectView(RedirectView):

    permanent = True

    def get_redirect_url(self):
        return self.request.get_full_path().replace("/cs", "")


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^admin/', include("massadmin.urls")),
    url(r'^advanced_filters/', include('advanced_filters.urls')),
    url(r'^adminactions/', include('adminactions.urls')),
    url(r"^su/", include("django_su.urls")),
    url(r'^selectable/', include('selectable.urls')),
    url(r'^oauth2/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    url(r'^redactor/', include('redactor.urls')),
    url(r'^nested_admin/', include('nested_admin.urls')),
    url(r'^rest/', include(router.urls)),
    url(r'^scribbler/', include('scribbler.urls')),
    url(r'^likes/', include('likes.urls')),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^rest-docs/', include_docs_urls(title='Do práce na kole API')),
    url(r'^', include("dpnk.urls")),
    url(r'^coupons/', include("coupons.urls")),
    url(r'^t_shirt/', include("t_shirt_delivery.urls")),
    url(r'^robots.txt$', lambda r: HttpResponse("User-agent: *\nAllow:", content_type="text/plain")),
    url(r'^', include('favicon.urls')),
    url(r'^cs/.*$', OldLanguageRedirectView.as_view()),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += i18n_patterns(
    url(r'^', include("dpnk.urls")),
    url(r'^', include("t_shirt_delivery.urls")),
    url(r'^', include("coupons.urls")),
    url('social/', include('social_django.urls', namespace='social')),
    url(r'^strava/', include("stravasync.urls")),
    prefix_default_language=False,
)

if 'rosetta' in settings.INSTALLED_APPS:
    urlpatterns += [
        url(r'^rosetta/', include('rosetta.urls')),
    ]

try:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
except ImportError:
    pass

handler403 = 'dpnk.exceptions.permission_denied_view'
