# flake8: noqa
# This is to allow * imports and thus DRY the code out.
from .base import *
from .registration_and_login import *
from .results_and_competitions import *
from .results_and_competitions import *
from .team import *
from .trips import *
from .map import *

__all__ = (
    # base
    UserAttendanceView,
    LandingView,
    LoggedInUsersListView,
    SwitchLang,
    status,
    test_errors,
    VueView,
    # team
    Company,
    UpdateTeam,
    UploadTeamPhoto,
    TeamMembers,
    OtherTeamMembers,
    approve_for_team,
    # trips
    SwitchRidesView,
    RidesView,
    RidesDetailsView,
    CalendarView,
    ApplicationView,
    EditTripView,
    UpdateTripView,
    CreateTripView,
    TripView,
    TripGeoJsonView,
    # registration and login
    DataReportView,
    DataReportResultsView,
    DPNKLoginView,
    ChangeTeamView,
    RegisterTeamView,
    RegisterCompanyView,
    RegisterSubsidiaryView,
    RegistrationAccessView,
    RegistrationView,
    ConfirmTeamInvitationView,
    PaymentTypeView,
    PaymentView,
    BeneficiaryPaymentView,
    PaymentResult,
    payment_status,
    PackageView,
    RegistrationProfileView,
    UpdateProfileView,
    TeamApprovalRequest,
    InviteView,
    FacebookLogin,
    GoogleLogin,
    # results and competitions
    DiplomasView,
    FrequencyView,
    CompetitionsRulesView,
    AdmissionsView,
    LengthCompetitionsView,
    FrequencyCompetitionsView,
    QuestionareCompetitionsView,
    CompetitionResultsView,
    QuestionnaireView,
    QuestionnaireAnswersAllView,
    questions,
    questionnaire_results,
    questionnaire_answers,
    answers,
    statistics,
    daily_chart,
    daily_distance_extra_json,
    CompetitorCountView,
    DrawResultsView,
    # map
    MapView,
)
