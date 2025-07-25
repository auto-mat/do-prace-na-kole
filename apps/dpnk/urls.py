# -*- coding: utf-8 -*-
# Author: Petr Dlouhý <petr.dlouhy@email.cz>
#
# Copyright (C) 2015 o.s. Auto*Mat
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from django.conf.urls import url, include
from django.urls import path, re_path
from django.contrib.auth import views as django_views
from django.utils.translation import ugettext_lazy as _

from . import auth
from . import company_admin_views
from . import views, views_results
from .autocomplete_views import (
    CompanyAutocomplete,
    SubsidiaryAutocomplete,
    TeamAutocomplete,
)
from .rest import (
    DataReportResults,
    DataReportResultsByChallenge,
    HasOrganizationAdmin,
    HasUserVerifiedEmailAddress,
    IsUserOrganizationAdmin,
    MyOrganizationAdmin,
    OpenApplicationWithRestToken,
    PayUCreateOrderPost,
    PayUPaymentNotifyPost,
    router,
    SendChallengeTeamInvitationEmailPost,
    SendRegistrationConfirmationEmail,
    StravaAuth,
    StravaConnect,
    StravaDisconnect,
)

from .rest_coordinator import (
    ApprovePaymentsView,
    GetAttendanceView,
    BoxRequestView,
    BoxRequestRemoveView,
    router as coordinator_router,
)

from .views import (
    answers,
    questionnaire_answers,
    questionnaire_results,
    questions,
    GoogleLogin,
    FacebookLogin,
)

from apps.dpnk.rest_registration import CustomRegisterView
from allauth.account.views import confirm_email


urlpatterns = [
    url(
        r"^tym/$",
        views.ChangeTeamView.as_view(),
        name="zmenit_tym",
    ),
    url(
        r"^company-autocomplete/$",
        CompanyAutocomplete.as_view(),
        name="company_autocomplete",
    ),
    url(
        r"^subsidiary-autocomplete/$",
        SubsidiaryAutocomplete.as_view(),
        name="subsidiary_autocomplete",
    ),
    url(
        r"^team-autocomplete/$",
        TeamAutocomplete.as_view(),
        name="team_autocomplete",
    ),
    url(
        r"^registrovat_spolecnost/$",
        views.RegisterCompanyView.as_view(),
        name="register_company",
    ),
    url(
        r"^registrovat_pobocku/(?P<company_id>\d*)$",
        views.RegisterSubsidiaryView.as_view(),
        name="register_subsidiary",
    ),
    url(
        r"^registrovat_tym/(?P<subsidiary_id>\d*)$",
        views.RegisterTeamView.as_view(),
        name="register_team",
    ),
    url(
        r"^upravit_tym/$",
        views.UpdateTeam.as_view(),
        name="edit_team",
    ),
    url(
        r"^upload_team_photo/$",
        views.UploadTeamPhoto.as_view(),
        name="upload_team_photo",
    ),
    url(
        r"^tym/(?P<token>[0-9A-Za-z]+)/(?P<initial_email>\S+@\S+\.\w+)/$$",
        views.ConfirmTeamInvitationView.as_view(),
        name="change_team_invitation",
    ),
    url(
        r"^registrace/$",
        views.RegistrationView.as_view(),
        {"success_url": "typ_platby"},
        name="registrace",
    ),
    url(
        r"^registrace/(?P<token>[0-9A-Za-z]+)/(?P<initial_email>\S+@\S+\.\w+)/$$",
        views.RegistrationView.as_view(),
        {"success_url": "typ_platby"},
        name="registrace",
    ),
    url(
        r"^registrace/(?P<initial_email>\S+@\S+\.\w+)/$$",
        views.RegistrationView.as_view(),
        {"success_url": "typ_platby"},
        name="registrace",
    ),
    url(
        r"^registrace_pristup/$",
        views.RegistrationAccessView.as_view(),
        name="registration_access",
    ),
    url(
        r"^pozvanky/$",
        views.InviteView.as_view(),
        {"success_url": "typ_platby"},
        name="pozvanky",
    ),
    url(
        r"^zaslat_zadost_clenstvi/$",
        views.TeamApprovalRequest.as_view(),
        name="zaslat_zadost_clenstvi",
    ),
    url(
        r"^registration_complete/$",
        views.RegistrationCompleteView.as_view(),
        name="dpnk_registration_complete",
    ),
    url(
        r"^jizdy$",
        views.RidesView.as_view(),
        name="rides",
    ),
    url(
        r"^jizdy-podrobne/$",
        views.RidesDetailsView.as_view(),
        name="rides_details",
    ),
    url(
        r"^kalendar/$",
        views.CalendarView.as_view(),
        name="calendar",
    ),
    url(
        r"^mapa/$",
        views.MapView.as_view(),
        name="map",
    ),
    url(
        r"^nekompletni$",
        views.RegistrationUncompleteForm.as_view(),
        name="registration_uncomplete",
    ),
    url(
        r"^dalsi_clenove/$",
        views.TeamMembers.as_view(),
        name="team_members",
    ),
    url(
        r"^dalsi_clenove_vysledky/$",
        views.OtherTeamMembers.as_view(
            template_name="dpnk/team_members_results.html",
        ),
        name="other_team_members_results",
    ),
    url(
        r"^spolecnost/$",
        views.Company.as_view(),
        name="company",
    ),
    url(
        r"^pravidelnost/$",
        views.FrequencyView.as_view(),
        name="team_frequency",
    ),
    url(
        r"^souteze_vykonnostni/$",
        views.LengthCompetitionsView.as_view(),
        name="length_competitions",
    ),
    url(
        r"^souteze_pravidelnostni/$",
        views.FrequencyCompetitionsView.as_view(),
        name="competitions",
    ),
    url(
        r"^dotaznikove_souteze/$",
        views.QuestionareCompetitionsView.as_view(),
        name="questionnaire_competitions",
    ),
    url(
        r"^souteze/pravidla/(?P<city_slug>[^&]+)/$",
        views.CompetitionsRulesView.as_view(
            template_name="dpnk/competitions_rules.html",
        ),
        name="competition-rules-city",
    ),
    url(
        r"^souteze/vysledky/(?P<city_slug>[^&]+)/$",
        views.CompetitionsRulesView.as_view(
            title_base=_("Výsledky soutěží"),
            template_name="dpnk/competitions_results_city.html",
        ),
        name="competition-results-city",
    ),
    url(
        r"^vysledky_souteze/(?P<competition_slug>[^&/]+)/$",
        views_results.CompetitionResultsView.as_view(),
        name="competition_results",
    ),
    url(
        r"^export_vysledky_souteze/(?P<competition_slug>[^&/]+)/(?P<extension>[0-9A-Za-z_\-]+)$",
        views_results.ExportCompetitionResults.as_view(),
        name="export_competition_results",
    ),
    url(
        r"^export_vysledky_souteze/(?P<competition_slug>[^&/]+)/(?P<extension>[0-9A-Za-z_\-]+)/(?P<organization>[0-9]+)$",
        views_results.ExportCompetitionResults.as_view(),
        name="export_competition_results",
    ),
    url(
        r"^vysledky_souteze_json/(?P<competition_slug>[^&/]+)/$",
        views_results.CompetitionResultListJson.as_view(),
        name="competition_result_list_json",
    ),
    url(
        r"^questionnaire_answers/(?P<competition_slug>[^&/]+)/$",
        views.QuestionnaireAnswersAllView.as_view(),
        name="questionnaire_answers_all",
    ),
    url(
        r"^otazka/(?P<questionnaire_slug>[0-9A-Za-z_\-]+)/$",
        views.QuestionnaireView.as_view(),
        name="questionnaire",
    ),
    url(
        r"^vytvorit_profil/$",
        views.RegistrationProfileView.as_view(),
        name="upravit_profil",
    ),
    url(
        r"^upravit_profil/$",
        views.UpdateProfileView.as_view(),
        name="edit_profile_detailed",
    ),
    url(
        r"^typ_platby/$",
        views.PaymentTypeView.as_view(),
        name="typ_platby",
    ),
    url(
        r"^platba/$",
        views.PaymentView.as_view(),
        name="payment",
    ),
    url(
        r"^platba-beneficni/$",
        views.BeneficiaryPaymentView.as_view(),
        name="payment_beneficiary",
    ),
    url(
        r"^diplomas/$",
        views.DiplomasView.as_view(),
        name="diplomas",
    ),
    url(
        r"^statistika/$",
        views.statistics,
    ),
    url(
        r"^denni-graf/$",
        views.daily_chart,
    ),
    url(
        r"^denni-vzdalenost/$",
        views.daily_distance_extra_json,
    ),
    url(
        r"^denni-vzdalenost-extra/$",
        views.daily_distance_extra_json,
    ),
    url(
        r"^pocty-soutezicich/$",
        views.CompetitorCountView.as_view(),
        name="competitor_counts",
    ),
    # url(
    #     r'^cykloservis/$',
    #     views.BikeRepairView.as_view(),
    #     name="bike_repair",
    # ),
    url(
        r"^package/$",
        views.PackageView.as_view(),
        name="package",
    ),
    url(
        r"^aplikace/$",
        views.ApplicationView.as_view(),
        name="application",
    ),
    url(
        r"^open-app-with-rest-token/(?P<app_id>[0-9]+)/$",
        views.OpenApplicationWithRestTokenView.as_view(),
        name="open-application-with-rest-token",
    ),
    url(
        r"^address/$",
        views.UserAttendanceView.as_view(
            template_name="dpnk/address.html",
        ),
    ),
    url(
        r"^trip/(?P<date>[^&/]+)/(?P<direction>[^&/]+)$",
        views.view_edit_trip,
        name="trip",
    ),
    url(
        r"^view_trip/(?P<date>[^&/]+)/(?P<direction>[^&/]+)$",
        views.TripView.as_view(),
        name="view_trip",
    ),
    url(
        r"^trip_geojson/(?P<date>[^&/]+)/(?P<direction>[^&/]+)$",
        views.TripGeoJsonView.as_view(),
        name="trip_geojson",
    ),
    url(
        r"^third_party_routes/$",
        views.ThirdPartyRoutesView.as_view(),
        name="third_party_routes",
    ),
    url(
        r"^emisni_kalkulacka/$",
        views.UserAttendanceView.as_view(
            template_name="dpnk/emission_calculator.html",
            title=_("Emisní kalkulačka"),
        ),
        name="emission_calculator",
    ),
    url(
        r"^help/$",
        views.UserAttendanceView.as_view(
            template_name="dpnk/help.html",
            title=_("Nápověda"),
        ),
        name="help",
    ),
    url(
        r"^$",
        views.LandingView.as_view(),
        name="profil",
    ),
    url(
        r"^status/$",
        views.status,
    ),
    url(
        r"^switch_lang/$",
        views.SwitchLang.as_view(),
        name="switch_lang",
    ),
    url(
        r"^switch_rides_view/$",
        views.SwitchRidesView.as_view(),
        name="switch_rides_view",
    ),
    path(
        "datareport/<challenge>/",
        views.DataReportView.as_view(),
        name="datareport",
    ),
    path(
        "datareport-results/<type>/",
        views.DataReportResultsView.as_view(),
        name="datareport-results",
    ),
    path(
        "rest/auth/",
        include("dj_rest_auth.urls"),
    ),
    path(
        "rest/auth/facebook/login/",
        FacebookLogin.as_view(),
        name="fb_login",
    ),
    path(
        "rest/auth/google/login/",
        GoogleLogin.as_view(),
        name="gg_login",
    ),
    path(
        "rest/auth/registration/",
        CustomRegisterView.as_view(),
        name="custom_register",
    ),
    re_path(
        r"^rest/auth/registration/account-confirm-email/(?P<key>[-:\w]+)/$",
        confirm_email,
        name="account_confirm_email",
    ),
    path(
        "rest/auth/registration/has-user-verified-email-address/",
        HasUserVerifiedEmailAddress.as_view(),
        name="has-user-verified-email-address",
    ),
    path(
        "rest/auth/registration/send-confirmation-email/",
        SendRegistrationConfirmationEmail.as_view(),
        name="send-registration-confirmation-email",
    ),
    path(
        "rest/payu-create-order/",
        PayUCreateOrderPost.as_view(),
        name="payu-create-order",
    ),
    path(
        "rest/payu-notify-order-status/",
        PayUPaymentNotifyPost.as_view(),
        name="payu-notify-order-status",
    ),
    path(
        "rest/is-user-organization-admin/",
        IsUserOrganizationAdmin.as_view(),
        name="is-user-organization-admin",
    ),
    path(
        "rest/has-organization-admin/<int:organization_id>/",
        HasOrganizationAdmin.as_view(),
        name="has-organization-admin",
    ),
    path(
        "rest/my-organization-admin/",
        MyOrganizationAdmin.as_view(),
        name="my-organization-admin",
    ),
    path(
        "rest/send-team-membership-invitation-email/",
        SendChallengeTeamInvitationEmailPost.as_view(),
        name="send-team-membership-invitation-email",
    ),
    path(
        "rest/open-app-with-rest-token/<int:app_id>/",
        OpenApplicationWithRestToken.as_view(),
        name="open-app-with-rest-token",
    ),
    re_path(
        "rest/strava-connect/(?P<scope>(read|read_all))/",
        StravaConnect.as_view(),
        name="strava-connect",
    ),
    path(
        "rest/strava-disconnect/",
        StravaDisconnect.as_view(),
        name="strava-disconnect",
    ),
    path(
        "rest/strava-auth/<str:code>/",
        StravaAuth.as_view(),
        name="strava-auth",
    ),
    re_path(
        "rest/datareport-results/(?P<report_type>("
        "regularity|team-regularity-city|performance-organization|performance-city|organizations-review))/",
        DataReportResults.as_view(),
        name="datareport-results-rest",
    ),
    re_path(
        "rest/datareport-results-by-challenge/(?P<challenge>(may|september-january))/",
        DataReportResultsByChallenge.as_view(),
        name="datareport-results-by-challenge",
    ),
    url(r"^account/", include("allauth.urls")),
    path("rest/auth/registration/", include("dj_rest_auth.registration.urls")),
    # company admin:
    url(
        r"^spolecnost/oficialni_souteze/$",
        company_admin_views.RelatedCompetitionsView.as_view(),
        name="company_admin_related_competitions",
    ),
    url(
        r"^spolecnost/zadost_admina/$",
        company_admin_views.CompanyAdminView.as_view(),
        name="company_admin_application",
    ),
    url(
        r"^spolecnost/soutez/(?P<competition_slug>[^&/]+)/$",
        company_admin_views.CompanyCompetitionView.as_view(),
        name="company_admin_competition",
    ),
    url(
        r"^upravit_pobocku/(?P<pk>[0-9]+)/$",
        company_admin_views.EditSubsidiaryView.as_view(),
        name="edit_subsidiary",
    ),
    url(
        r"^spolecnost/soutez/$",
        company_admin_views.CompanyCompetitionView.as_view(),
        name="company_admin_competition",
    ),
    url(
        r"^spolecnost/struktura/$",
        company_admin_views.CompanyStructure.as_view(),
        name="company_structure",
    ),
    url(
        r"^spolecnost/struktura/export/(?P<extension>csv|xls|ods)/$",
        company_admin_views.UserAttendanceExportView.as_view(),
        name="company_export",
    ),
    url(
        r"^spolecnost/souteze/$",
        company_admin_views.CompanyCompetitionsShowView.as_view(),
        name="company_admin_competitions",
    ),
    url(
        r"^faktury/$",
        company_admin_views.InvoicesView.as_view(),
        name="invoices",
    ),
    url(
        r"^zaplatit_za_uzivatele/$",
        company_admin_views.SelectUsersPayView.as_view(),
        name="company_admin_pay_for_users",
    ),
    url(
        r"^spolecnost/editovat_spolecnost/$",
        company_admin_views.CompanyEditView.as_view(),
        name="edit_company",
    ),
    url(
        r"^spolecnost/registrace_admina/$",
        company_admin_views.CompanyAdminApplicationView.as_view(),
        name="register_admin",
    ),
    url(
        r"^login/(?P<initial_email>[^&]+)/$$",
        views.DPNKLoginView.as_view(
            form_class=auth.AuthenticationFormDPNK,
            template_name="dpnk/base_login_registration.html",
        ),
        name="login",
    ),
    url(
        r"^login/?$",
        views.DPNKLoginView.as_view(
            form_class=auth.AuthenticationFormDPNK,
            template_name="dpnk/base_login_registration.html",
        ),
        name="login",
    ),
    url(
        r"^logout/$",
        django_views.LogoutView.as_view(),
        name="logout",
    ),
    url(
        r"^platba_status$",
        views.payment_status,
        name="payment_status",
    ),
    url(
        r"^platba_uspesna/(?P<trans_id>[0-9]+)/(?P<session_id>[0-9A-Za-z\-]+)/(?P<pay_type>[0-9A-Za-z]+)/$$",
        views.PaymentResult.as_view(),
        {"success": True},
        name="payment_successfull",
    ),
    url(
        r"^platba_neuspesna/(?P<trans_id>[0-9]*)/(?P<session_id>[0-9A-Za-z\-]+)/(?P<pay_type>[0-9A-Za-z]*)/(?P<error>[^&]+)/$$",
        views.PaymentResult.as_view(),
        {"success": False},
        name="payment_unsuccessfull",
    ),
    url(
        r"^zapomenute_heslo/$",
        django_views.PasswordResetView.as_view(form_class=auth.PasswordResetForm),
        name="password_reset",
    ),
    url(
        r"^zapomenute_heslo/odeslano/$",
        django_views.PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    url(
        r"^zapomenute_heslo/zmena/(?P<uidb64>[=0-9A-Za-z_]+)-(?P<token>.+)/$",
        django_views.PasswordResetConfirmView.as_view(form_class=auth.SetPasswordForm),
        name="password_reset_confirm",
    ),
    url(
        r"^zapomenute_heslo/dokonceno/$",
        django_views.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    url(
        r"^zmena_hesla/$",
        auth.PasswordChangeView.as_view(),
        name="password_change",
    ),
    url(
        r"^zmena_hesla_hotovo/$",
        django_views.PasswordChangeDoneView.as_view(),
        name="password_change_done",
    ),
    url(
        r"^test_errors/$",
        views.test_errors,
        name="test_errors",
    ),
    # city coordinator urls
    url(
        r"^coordinators/$",
        views.VueView.as_view(
            title=_("Města které koordinujete"),
        ),
        name="company_coordinator",
    ),
    # admin urls
    url(
        r"^admin/answers/$",
        answers,
        name="admin_answers",
    ),
    url(
        r"^admin/questions/$",
        questions,
        name="admin_questions",
    ),
    url(
        r"^admin/dotaznik_odpovedi/(?P<competition_slug>[^&/]+)$",
        questionnaire_answers,
        name="admin_questionnaire_answers",
    ),
    url(
        r"^admin/dotaznik/(?P<competition_slug>[^&/]+)/$",
        questionnaire_results,
        name="admin_questionnaire_results",
    ),
    url(
        r"^admin/losovani/(?P<competition_slug>[^&/]+)/$",
        views.DrawResultsView.as_view(),
        name="admin_draw_results",
    ),
    url(
        r"^admin/logged-in-user-list/$",
        views.LoggedInUsersListView.as_view(),
        name="logged_in_user_list",
    ),
    # REST API
    path("rest/", include(router.urls), name="rest_api"),
    path(
        "rest/coordinator/",
        include(coordinator_router.urls),
        name="coordinator_rest_api",
    ),
    path(
        "rest/coordinator/approve-payments/",
        ApprovePaymentsView.as_view(),
        name="approve-payments",
    ),
    path(
        "rest/coordinator/get-attendance/",
        GetAttendanceView.as_view(),
        name="get-attendance",
    ),
    path(
        "rest/coordinator/package-request/",
        BoxRequestView.as_view(),
        name="package-request",
    ),
    path(
        "rest/coordinator/package-request/remove",
        BoxRequestRemoveView.as_view(),
        name="package-request-remove",
    ),
]
