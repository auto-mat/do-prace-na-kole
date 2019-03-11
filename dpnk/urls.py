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

from django.conf.urls import url
from django.contrib.auth import views as django_views
from django.utils.translation import ugettext_lazy as _

from . import auth
from . import company_admin_views
from . import views, views_results
from .views import answers, questionnaire_answers, questionnaire_results, questions
urlpatterns = [
    url(
        r'^tym/$',
        views.ChangeTeamView.as_view(),
        name="zmenit_tym",
    ),
    url(
        r'^registrovat_spolecnost/$',
        views.RegisterCompanyView.as_view(),
        name="register_company",
    ),
    url(
        r'^registrovat_pobocku/(?P<company_id>\d*)$',
        views.RegisterSubsidiaryView.as_view(),
        name="register_subsidiary",
    ),
    url(
        r'^registrovat_tym/(?P<subsidiary_id>\d*)$',
        views.RegisterTeamView.as_view(),
        name="register_team",
    ),
    url(
        r'^upravit_tym/$',
        views.UpdateTeam.as_view(),
        name="edit_team",
    ),
    url(
        r'^upload_team_photo/$',
        views.UploadTeamPhoto.as_view(),
        name="upload_team_photo",
    ),
    url(
        r'^tym/(?P<token>[0-9A-Za-z]+)/(?P<initial_email>[^&]+)/$$',
        views.ConfirmTeamInvitationView.as_view(),
        name="change_team_invitation",
    ),
    url(
        r'^registrace/$',
        views.RegistrationView.as_view(),
        {'success_url': 'typ_platby'},
        name="registrace",
    ),
    url(
        r'^registrace/(?P<token>[0-9A-Za-z]+)/(?P<initial_email>[^&/]+)/$$',
        views.RegistrationView.as_view(),
        {'success_url': 'typ_platby'},
        name="registrace",
    ),
    url(
        r'^registrace/(?P<initial_email>[^&]+)/$$',
        views.RegistrationView.as_view(),
        {'success_url': 'typ_platby'},
        name="registrace",
    ),
    url(
        r'^registrace_pristup/$',
        views.RegistrationAccessView.as_view(),
        name="registration_access",
    ),
    url(
        r'^pozvanky/$',
        views.InviteView.as_view(),
        {'success_url': 'typ_platby'},
        name="pozvanky",
    ),
    url(
        r'^zaslat_zadost_clenstvi/$',
        views.TeamApprovalRequest.as_view(),
        name="zaslat_zadost_clenstvi",
    ),
    url(
        r'^jizdy$',
        views.RidesView.as_view(),
        name="rides",
    ),
    url(
        r'^jizdy-podrobne/$',
        views.RidesDetailsView.as_view(),
        name="rides_details",
    ),
    url(
        r'^kalendar/$',
        views.VacationsView.as_view(),
        name="calendar",
    ),
    url(
        r'^nekompletni$',
        views.RegistrationUncompleteForm.as_view(),
        name="registration_uncomplete",
    ),
    url(
        r'^dalsi_clenove/$',
        views.TeamMembers.as_view(),
        name="team_members",
    ),
    url(
        r'^dalsi_clenove_vysledky/$',
        views.OtherTeamMembers.as_view(
            template_name='registration/team_members_results.html',
        ),
        name="other_team_members_results",
    ),
    url(
        r'^souteze_vykonnostni/$',
        views.LengthCompetitionsView.as_view(),
        name="length_competitions",
    ),
    url(
        r'^souteze_pravidelnostni/$',
        views.FrequencyCompetitionsView.as_view(),
        name="competitions",
    ),
    url(
        r'^dotaznikove_souteze/$',
        views.QuestionareCompetitionsView.as_view(),
        name="questionnaire_competitions",
    ),
    url(
        r'^souteze/pravidla/(?P<city_slug>[^&]+)/$',
        views.CompetitionsRulesView.as_view(
            template_name="registration/competitions_rules.html",
        ),
        name="competition-rules-city",
    ),
    url(
        r'^souteze/vysledky/(?P<city_slug>[^&]+)/$',
        views.CompetitionsRulesView.as_view(
            title_base=_("Výsledky soutěží"),
            template_name="registration/competitions_results_city.html",
        ),
        name="competition-results-city",
    ),
    url(
        r'^vysledky_souteze/(?P<competition_slug>[^&/]+)/$',
        views_results.CompetitionResultsView.as_view(),
        name="competition_results",
    ),
    url(
        r'^export_vysledky_souteze/(?P<competition_slug>[^&/]+)/(?P<extension>[0-9A-Za-z_\-]+)$',
        views_results.ExportCompetitionResults.as_view(),
        name='export_competition_results',
    ),
    url(
        r'^export_vysledky_souteze/(?P<competition_slug>[^&/]+)/(?P<extension>[0-9A-Za-z_\-]+)/(?P<organization>[0-9]+)$',
        views_results.ExportCompetitionResults.as_view(),
        name='export_competition_results',
    ),
    url(
        r'^vysledky_souteze_json/(?P<competition_slug>[^&/]+)/$',
        views_results.CompetitionResultListJson.as_view(),
        name='competition_result_list_json',
    ),
    url(
        r'^questionnaire_answers/(?P<competition_slug>[^&/]+)/$',
        views.QuestionnaireAnswersAllView.as_view(),
        name="questionnaire_answers_all",
    ),
    url(
        r'^otazka/(?P<questionnaire_slug>[0-9A-Za-z_\-]+)/$',
        views.QuestionnaireView.as_view(),
        name="questionnaire",
    ),
    url(
        r'^vytvorit_profil/$',
        views.RegistrationProfileView.as_view(),
        name="upravit_profil",
    ),
    url(
        r'^upravit_profil/$',
        views.UpdateProfileView.as_view(),
        name="edit_profile_detailed",
    ),
    url(
        r'^upravit_trasu/$',
        views.UpdateTrackView.as_view(),
        name="upravit_trasu",
    ),
    url(
        r'^typ_platby/$',
        views.PaymentTypeView.as_view(),
        name="typ_platby",
    ),
    url(
        r'^platba/$',
        views.PaymentView.as_view(),
        name="payment",
    ),
    url(
        r'^platba-beneficni/$',
        views.BeneficiaryPaymentView.as_view(),
        name="payment_beneficiary",
    ),
    url(
        r'^diplomas/$',
        views.DiplomasView.as_view(),
        name="diplomas",
    ),
    url(
        r'^statistika/$',
        views.statistics,
    ),
    url(
        r'^denni-graf/$',
        views.daily_chart,
    ),
    url(
        r'^denni-vzdalenost/$',
        views.daily_distance_extra_json,
    ),
    url(
        r'^denni-vzdalenost-extra/$',
        views.daily_distance_extra_json,
    ),
    url(
        r'^pocty-soutezicich/$',
        views.CompetitorCountView.as_view(),
        name="competitor_counts",
    ),
    url(
        r'^cykloservis/$',
        views.BikeRepairView.as_view(),
        name="bike_repair",
    ),
    url(
        r'^package/$',
        views.PackageView.as_view(),
        name="package",
    ),
    url(
        r'^aplikace/$',
        views.ApplicationView.as_view(),
        name="application",
    ),
    url(
        r'^address/$',
        views.UserAttendanceView.as_view(
            template_name="registration/address.html",
        ),
    ),
    url(
        r'^tracks/$',
        views.CombinedTracksKMLView.as_view(),
    ),
    url(
        r'^tracks/(?P<city_slug>[^&]+)/$',
        views.CombinedTracksKMLView.as_view(),
    ),
    url(
        r'^trip/(?P<date>[^&/]+)/(?P<direction>[^&/]+)$',
        views.view_edit_trip,
        name="trip",
    ),
    url(
        r'^trip_geojson/(?P<date>[^&/]+)/(?P<direction>[^&/]+)$',
        views.TripGeoJsonView.as_view(),
        name="trip_geojson",
    ),
    url(
        r'^emisni_kalkulacka/$',
        views.UserAttendanceView.as_view(
            template_name="registration/emission_calculator.html",
            title=_(u"Emisní kalkulačka"),
        ),
        name="emission_calculator",
    ),
    url(
        r'^help/$',
        views.UserAttendanceView.as_view(
            template_name="registration/help.html",
            title=_("Nápověda"),
        ),
        name="help",
    ),
    url(
        r'^$',
        views.RegistrationCompleteUserAttendanceView.as_view(
            template_name="registration/landing.html",
            title=_("Vítejte v dalším ročníku soutěže!"),
        ),
        name="profil",
    ),
    url(
        r'^status/$',
        views.status,
    ),


    # company admin:
    url(
        r'^spolecnost/oficialni_souteze/$',
        company_admin_views.RelatedCompetitionsView.as_view(),
        name="company_admin_related_competitions",
    ),
    url(
        r'^spolecnost/zadost_admina/$',
        company_admin_views.CompanyAdminView.as_view(),
        name='company_admin_application',
    ),
    url(
        r'^spolecnost/soutez/(?P<competition_slug>[^&/]+)/$',
        company_admin_views.CompanyCompetitionView.as_view(),
        name="company_admin_competition",
    ),
    url(
        r'^upravit_pobocku/(?P<pk>[0-9]+)/$',
        company_admin_views.EditSubsidiaryView.as_view(),
        name="edit_subsidiary",
    ),
    url(
        r'^spolecnost/soutez/$',
        company_admin_views.CompanyCompetitionView.as_view(),
        name="company_admin_competition",
    ),
    url(
        r'^spolecnost/struktura/$',
        company_admin_views.CompanyStructure.as_view(),
        name="company_structure",
    ),
    url(
        r'^spolecnost/struktura/export/(?P<extension>csv|xls|ods)/$',
        company_admin_views.UserAttendanceExportView.as_view(),
        name="company_export",
    ),
    url(
        r'^spolecnost/souteze/$',
        company_admin_views.CompanyCompetitionsShowView.as_view(),
        name="company_admin_competitions",
    ),
    url(
        r'^faktury/$',
        company_admin_views.InvoicesView.as_view(),
        name="invoices",
    ),
    url(
        r'^zaplatit_za_uzivatele/$',
        company_admin_views.SelectUsersPayView.as_view(),
        name='company_admin_pay_for_users',
    ),
    url(
        r'^spolecnost/editovat_spolecnost/$',
        company_admin_views.CompanyEditView.as_view(),
        name="edit_company",
    ),
    url(
        r'^spolecnost/registrace_admina/$',
        company_admin_views.CompanyAdminApplicationView.as_view(),
        name="register_admin",
    ),
    url(
        r'^login/(?P<initial_email>[^&]+)/$$',
        views.DPNKLoginView.as_view(
            form_class=auth.AuthenticationFormDPNK,
            template_name='base_generic_form.html',
        ),
        name='login',
    ),
    url(
        r'^login/?$',
        views.DPNKLoginView.as_view(
            form_class=auth.AuthenticationFormDPNK,
            template_name='base_generic_form.html',
        ),
        name='login',
    ),
    url(
        r'^logout/$',
        django_views.LogoutView.as_view(),
        name='logout',
    ),
    url(
        r'^platba_status$',
        views.payment_status,
        name="payment_status",
    ),
    url(
        r'^platba_uspesna/(?P<trans_id>[0-9]+)/(?P<session_id>[0-9A-Za-z\-]+)/(?P<pay_type>[0-9A-Za-z]+)/$$',
        views.PaymentResult.as_view(),
        {'success': True},
        name="payment_successfull",
    ),
    url(
        r'^platba_neuspesna/(?P<trans_id>[0-9]*)/(?P<session_id>[0-9A-Za-z\-]+)/(?P<pay_type>[0-9A-Za-z]*)/(?P<error>[^&]+)/$$',
        views.PaymentResult.as_view(),
        {'success': False},
        name="payment_unsuccessfull",
    ),
    url(
        r'^zapomenute_heslo/$',
        django_views.PasswordResetView.as_view(form_class=auth.PasswordResetForm),
        name='password_reset',
    ),
    url(
        r'^zapomenute_heslo/odeslano/$',
        django_views.PasswordResetDoneView.as_view(),
        name='password_reset_done',
    ),
    url(
        r'^zapomenute_heslo/zmena/(?P<uidb64>[=0-9A-Za-z_]+)-(?P<token>.+)/$',
        django_views.PasswordResetConfirmView.as_view(form_class=auth.SetPasswordForm),
        name='password_reset_confirm',
    ),
    url(
        r'^zapomenute_heslo/dokonceno/$',
        django_views.PasswordResetCompleteView.as_view(),
        name='password_reset_complete',
    ),
    url(
        r'^zmena_hesla/$',
        auth.PasswordChangeView.as_view(),
        name='password_change',
    ),
    url(
        r'^zmena_hesla_hotovo/$',
        django_views.PasswordChangeDoneView.as_view(),
        name='password_change_done',
    ),

    # admin urls
    url(
        r'^admin/answers/$',
        answers,
        name='admin_answers',
    ),
    url(
        r'^admin/questions/$',
        questions,
        name='admin_questions',
    ),
    url(
        r'^admin/dotaznik_odpovedi/(?P<competition_slug>[^&/]+)$',
        questionnaire_answers,
        name='admin_questionnaire_answers',
    ),
    url(
        r'^admin/dotaznik/(?P<competition_slug>[^&/]+)/$',
        questionnaire_results,
        name='admin_questionnaire_results',
    ),
    url(
        r'^admin/losovani/(?P<competition_slug>[^&/]+)/$',
        views.DrawResultsView.as_view(),
        name="admin_draw_results",
    ),
]
