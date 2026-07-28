# -*- coding: utf-8 -*-
# Author: Timothy Hobbs <timothy <at> hobbs.cz>

from django import http
from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import generic
from django.views.generic.base import TemplateView

from dpnk.util import get_base_url
from dpnk.views_permission_mixins import RegistrationCompleteMixin

import requests.exceptions

import stravalib
from stravalib.exc import AccessUnauthorized, RateLimitExceeded

from . import hashtags
from . import models
from . import tasks


class AboutStrava(RegistrationCompleteMixin, TemplateView):
    template_name = "stravasync/about.html"
    title = _("Propojení se Stravou")
    registration_phase = "application"

    def __init__(self, *args, **kwargs):
        self.sync = False
        return super().__init__(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.sync = request.POST.get("sync", False)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = {
            "title": self.title,
            "campaign_slug": self.request.subdomain,
            "hashtag_to": hashtags.get_hashtag_to(
                self.request.subdomain, self.request.LANGUAGE_CODE
            ),
            "hashtag_from": hashtags.get_hashtag_from(
                self.request.subdomain, self.request.LANGUAGE_CODE
            ),
        }
        try:
            stravaaccount = self.request.user.stravaaccount
            if (
                (self.sync or (stravaaccount.last_sync_time is None))
                and stravaaccount.user_sync_count < settings.STRAVA_MAX_USER_SYNC_COUNT
            ):
                try:
                    context["sync_outcome"] = tasks.sync(
                        self.request.user.stravaaccount.id
                    )
                except requests.exceptions.ConnectionError:
                    context["sync_failed"] = _("Aplikace Strava není dostupná.")
                except RateLimitExceeded:
                    context["sync_failed"] = _("API limit vyčerpan.")
            context["account"] = {
                "username": stravaaccount.strava_username,
                "first_name": stravaaccount.first_name,
                "last_name": stravaaccount.last_name,
                "last_sync_time": stravaaccount.last_sync_time.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                if stravaaccount.last_sync_time
                else None,
                "user_sync_count": stravaaccount.user_sync_count,
            }
            context["warn_user_sync_count"] = settings.STRAVA_MAX_USER_SYNC_COUNT / 2
            context["max_user_sync_count"] = settings.STRAVA_MAX_USER_SYNC_COUNT
            context["app_redirect"] = reverse(
                "open-application-with-rest-token", args=("2")
            )
        except models.StravaAccount.DoesNotExist:
            context["account"] = {}
            context["authorize_href"] = reverse("strava_connect")
        return context


class StravaAuth(RegistrationCompleteMixin, generic.View):
    def get(self, request, *args, **kwargs):
        sclient = stravalib.Client()
        code = request.GET.get("code", None)
        token_response = sclient.exchange_code_for_token(
            client_id=settings.STRAVA_CLIENT_ID,
            client_secret=settings.STRAVA_CLIENT_SECRET,
            code=code,
        )
        acct, _ = models.StravaAccount.objects.get_or_create(
            user_id=request.user.id,
        )
        acct.strava_username = sclient.get_athlete().username or ""
        acct.first_name = sclient.get_athlete().firstname or ""
        acct.last_name = sclient.get_athlete().lastname or ""
        acct.access_token = token_response["access_token"]
        acct.refresh_token = token_response["refresh_token"]
        acct.save()
        return http.HttpResponseRedirect(reverse("about_strava"))


class StravaConnect(RegistrationCompleteMixin, generic.View):
    def post(self, request, *args, **kwargs):
        sclient = stravalib.Client()
        if request.POST.get("private", False):
            scope = "activity:read_all"
        else:
            scope = "activity:read"
        return http.HttpResponseRedirect(
            sclient.authorization_url(
                client_id=settings.STRAVA_CLIENT_ID,
                redirect_uri=get_base_url(self.request)
                + "/"
                + reverse("strava_auth")[1:],
                scope=scope,
            ),
        )


class StravaDisconnect(RegistrationCompleteMixin, generic.View):
    def post(self, request, *args, **kwargs):
        try:
            strava_account = request.user.stravaaccount
        except models.StravaAccount.DoesNotExist:
            return http.HttpResponseRedirect(reverse("about_strava"))
        sclient = stravalib.Client(access_token=strava_account.access_token)
        try:
            sclient.deauthorize()
        except AccessUnauthorized:
            pass
        strava_account.delete()
        return http.HttpResponseRedirect(reverse("about_strava"))
