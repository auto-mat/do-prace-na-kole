from django.conf import settings
from django.urls import include, re_path
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib.gis import admin
from django.http import HttpResponse
from django.urls import path
from django.views.generic import RedirectView

from dpnk.rest import router, PhotoURLGet

import notifications.urls

import rest_framework.authtoken.views

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
    re_path(r"^admin/", include("massadmin.urls")),
    re_path(r"^advanced_filters/", include("advanced_filters.urls")),
    re_path(r"^su/", include("django_su.urls")),
    re_path(r"^selectable/", include("selectable.urls")),
    re_path(r"^oauth2/", include("oauth2_provider.urls", namespace="oauth2_provider")),
    re_path(r"^photologue/", include("photologue.urls", namespace="photologue")),
    re_path(r"^redactor/", include("redactor.urls")),
    re_path(r"^nested_admin/", include("nested_admin.urls")),
    re_path(r"^rest/", include(router.urls)),
    re_path(r"^rest/photo-url/(?P<photo_url>.+)", PhotoURLGet.as_view()),
    re_path(r"^likes/", include("likes.urls")),
    re_path(r"^avatar/", include("avatar.urls")),
    re_path(r"^api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path("api-token-auth/", rest_framework.authtoken.views.obtain_auth_token),
    path("dj-rest-auth/", include("dj_rest_auth.urls")),
    re_path(r"^", include("dpnk.urls")),
    re_path(r"^coupons/", include("coupons.urls")),
    re_path(r"^donation/", include("donation_chooser.urls")),
    re_path(r"^t_shirt/", include("t_shirt_delivery.urls")),
    re_path(
        r"^robots.txt$",
        lambda r: HttpResponse("User-agent: *\nAllow:", content_type="text/plain"),
    ),
    re_path(r"^", include("favicon.urls")),
    re_path(r"^cs/.*$", OldLanguageRedirectView.as_view()),
    re_path(r"^register/", include("registration.backends.default.urls")),
    re_path(
        "^inbox/notifications/", include(notifications.urls, namespace="notifications")
    ),
    re_path(r"^report_builder/", include("report_builder.urls")),
    re_path(
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
    urlpatterns.append(re_path(r"^adminactions/", include("adminactions.urls")))
except NameError:
    pass

urlpatterns += i18n_patterns(
    re_path(r"^", include("dpnk.urls")),
    re_path(r"^", include("t_shirt_delivery.urls")),
    re_path(r"^", include("coupons.urls")),
    path("social/", include("social_django.urls", namespace="social")),
    re_path(r"^strava/", include("stravasync.urls")),
    re_path(r"^admin/", admin.site.urls),
    prefix_default_language=False,
)

if "rosetta" in settings.INSTALLED_APPS:
    urlpatterns += [
        re_path(r"^rosetta/", include("rosetta.urls")),
    ]

try:
    import debug_toolbar

    urlpatterns += [
        re_path(r"^__debug__/", include(debug_toolbar.urls)),
    ]
except ImportError:
    pass

handler403 = "dpnk.exceptions.permission_denied_view"

if getattr(settings, "SILK", False):
    urlpatterns += [
        re_path(r"^silk/", include("silk.urls", namespace="silk")),
    ]
