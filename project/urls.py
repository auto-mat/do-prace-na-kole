from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib.gis import admin
from django.http import HttpResponse
from django.urls import path
from django.views.generic import RedirectView

from dpnk.rest import router, PhotoURLGet

import notifications.urls

import rest_framework.authtoken.views
from rest_framework.documentation import include_docs_urls

admin.autodiscover()

from django.urls import re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


schema_view = get_schema_view(
    openapi.Info(
        title="Snippets API",
        default_version="v1",
        description="Test description",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


class OldLanguageRedirectView(RedirectView):

    permanent = True

    def get_redirect_url(self):
        return self.request.get_full_path().replace("/cs", "")


urlpatterns = [
    url(r"^admin/", include("massadmin.urls")),
    url(r"^advanced_filters/", include("advanced_filters.urls")),
    url(r"^su/", include("django_su.urls")),
    url(r"^selectable/", include("selectable.urls")),
    url(r"^oauth2/", include("oauth2_provider.urls", namespace="oauth2_provider")),
    path("admin_tools_stats/", include("admin_tools_stats.urls")),
    url(r"^photologue/", include("photologue.urls", namespace="photologue")),
    url(r"^redactor/", include("redactor.urls")),
    url(r"^nested_admin/", include("nested_admin.urls")),
    url(r"^rest/", include(router.urls)),
    url(r"^rest/photo-url/(?P<photo_url>.+)", PhotoURLGet.as_view()),
    url(r"^likes/", include("likes.urls")),
    url(r"^avatar/", include("avatar.urls")),
    url(r"^api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path("api-token-auth/", rest_framework.authtoken.views.obtain_auth_token),
    path("dj-rest-auth/", include("dj_rest_auth.urls")),
    url(r"^rest-docs/", include_docs_urls(title="Do práce na kole API")),
    url(r"^", include("dpnk.urls")),
    url(r"^coupons/", include("coupons.urls")),
    url(r"^donation/", include("donation_chooser.urls")),
    url(r"^t_shirt/", include("t_shirt_delivery.urls")),
    url(
        r"^robots.txt$",
        lambda r: HttpResponse("User-agent: *\nAllow:", content_type="text/plain"),
    ),
    url(r"^", include("favicon.urls")),
    url(r"^cs/.*$", OldLanguageRedirectView.as_view()),
    url(r"^register/", include("registration.backends.default.urls")),
    url(
        "^inbox/notifications/", include(notifications.urls, namespace="notifications")
    ),
    url(r"^report_builder/", include("report_builder.urls")),
    url(
        r"^" + settings.LOADER_IO_KEY + "/",
        lambda r: HttpResponse(settings.LOADER_IO_KEY, content_type="text/plain"),
    ),
    path(
        "rest/swagger<format>/",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    path(
        "rest/swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path(
        "rest/redoc/",
        schema_view.with_ui("redoc", cache_timeout=0),
        name="schema-redoc",
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

try:
    urlpatterns.append(url(r"^adminactions/", include("adminactions.urls")))
except NameError:
    pass

urlpatterns += i18n_patterns(
    url(r"^", include("dpnk.urls")),
    url(r"^", include("t_shirt_delivery.urls")),
    url(r"^", include("coupons.urls")),
    url("social/", include("social_django.urls", namespace="social")),
    url(r"^strava/", include("stravasync.urls")),
    url(r"^admin/", admin.site.urls),
    prefix_default_language=False,
)

if "rosetta" in settings.INSTALLED_APPS:
    urlpatterns += [
        url(r"^rosetta/", include("rosetta.urls")),
    ]

try:
    import debug_toolbar

    urlpatterns += [
        url(r"^__debug__/", include(debug_toolbar.urls)),
    ]
except ImportError:
    pass

handler403 = "dpnk.exceptions.permission_denied_view"

if getattr(settings, "SILK", False):
    urlpatterns += [
        url(r"^silk/", include("silk.urls", namespace="silk")),
    ]
