import datetime
import json

# Django imports
from braces.views import LoginRequiredMixin

from django.conf import settings
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import BooleanField, Case, Q, When
from django.forms.models import BaseModelFormSet
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import cache_control, never_cache
from django.views.generic.base import TemplateView, View
from django.views.generic.edit import CreateView, UpdateView

from extra_views import ModelFormSetView

# Local imports
from .. import calendar
from .. import exceptions
from .. import forms
from .. import models
from .. import results
from .. import util
from ..forms import UserProfileRidesUpdateForm
from ..models import Trip
from ..rest import TripSerializer
from ..views_mixins import (
    RegistrationMessagesMixin,
    TitleViewMixin,
    UserAttendanceParameterMixin,
)
from ..views_permission_mixins import (
    RegistrationCompleteMixin,
    registration_complete_gate,
)


class SwitchRidesView(LoginRequiredMixin, View):
    def dispatch(self, *args, **kwargs):
        if not self.request.user.is_anonymous:
            user_profile = self.request.user_attendance.userprofile
            if "rides_view" in self.request.GET:
                form = UserProfileRidesUpdateForm(
                    data={
                        "default_rides_view": self.request.GET.get("rides_view", None)
                    },
                    instance=user_profile,
                )
                if form.is_valid():
                    form.save()
            if user_profile.default_rides_view:
                view_mapping = {
                    "table": "rides",
                    "calendar": "calendar",
                }
                return redirect(view_mapping[user_profile.default_rides_view])
        return redirect("calendar")


#######################################
# Table ###############################
#######################################
class RidesFormSet(BaseModelFormSet):
    def total_form_count(self):
        form_count = super().total_form_count()
        if hasattr(self, "forms_max_number"):
            return min(self.forms_max_number, form_count)
        return form_count

    @property
    def initial_forms(self):
        """Return a list of all the initial forms in this formset."""
        return [form for form in self.forms if form.instance.pk is not None]

    @property
    def extra_forms(self):
        """Return a list of all the extra forms in this formset."""
        return [form for form in self.forms if form.instance.pk is None]


class RidesView(
    LoginRequiredMixin,
    RegistrationCompleteMixin,
    TitleViewMixin,
    RegistrationMessagesMixin,
    SuccessMessageMixin,
    ModelFormSetView,
):
    model = Trip
    form_class = forms.TripForm
    formset_class = RidesFormSet
    fields = (
        "commute_mode",
        "distance",
        "duration",
        "direction",
        "user_attendance",
        "date",
    )
    uncreated_trips = []
    success_message = _("Tabulka jízd úspěšně změněna")
    registration_phase = "profile_view"
    template_name = "dpnk/competition_profile.html"
    title = ""

    @method_decorator(never_cache)
    @method_decorator(cache_control(max_age=0, no_cache=True, no_store=True))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def has_allow_adding_rides(self):
        if not hasattr(self, "allow_adding_rides"):  # cache result
            self.allow_adding_rides = models.CityInCampaign.objects.get(
                city=self.user_attendance.team.subsidiary.city,
                campaign=self.user_attendance.campaign,
            ).allow_adding_rides
        return self.allow_adding_rides

    def get_queryset(self):
        if self.has_allow_adding_rides():
            self.trips, self.uncreated_trips = self.user_attendance.get_active_trips()
            trips = self.trips.annotate(  # fetch only needed fields
                track_isnull=Case(
                    When(track__isnull=True, then=True),
                    default=False,
                    output_field=BooleanField(),
                ),
            ).defer("track", "gpx_file")
            return trips
        else:
            return models.Trip.objects.none()

    def get_initial(self):
        distance = self.user_attendance.get_distance()
        no_work = models.CommuteMode.objects.get(slug="no_work")
        by_other_vehicle = models.CommuteMode.objects.get(slug="by_other_vehicle")
        return [
            {
                "distance": distance,
                "date": trip[0],
                "direction": trip[1],
                "user_attendance": self.user_attendance,
                "commute_mode": by_other_vehicle
                if util.working_day(trip[0])
                else no_work,
            }
            for trip in self.uncreated_trips
        ]

    def get_factory_kwargs(self):
        kwargs = super().get_factory_kwargs()
        kwargs["extra"] = len(self.uncreated_trips)
        return kwargs

    def post(self, request, *args, **kwargs):
        ret_val = super().post(request, args, kwargs)
        # TODO: use Celery for this
        results.recalculate_result_competitor(self.user_attendance)
        return ret_val

    def construct_formset(self):
        formset = super().construct_formset()
        formset.forms = [
            form for form in formset.forms if ("direction" in form.initial)
        ]
        formset.forms_max_number = len(formset.forms)

        formset.forms = sorted(
            formset.forms,
            key=lambda form: form.initial["direction"] or form.instance.direction,
            reverse=True,
        )
        formset.forms = sorted(
            formset.forms,
            key=lambda form: form.initial["date"] or form.instance.date,
            reverse=True,
        )
        return formset

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        city_slug = self.user_attendance.team.subsidiary.city.get_wp_slug()
        campaign = self.user_attendance.campaign
        context_data["questionnaire_answer"] = (
            models.Answer.objects.filter(
                Q(attachment__icontains=".jpg")
                | Q(attachment__icontains=".jpeg")
                | Q(attachment__icontains=".png")
                | Q(attachment__icontains=".gif")
                | Q(attachment__icontains=".bmp")
                | Q(attachment__icontains=".tiff"),
                question__competition__city=None,
                question__competition__competition_type="questionnaire",
                question__competition__campaign=campaign,
                attachment__isnull=False,
            )
            .exclude(
                attachment="",
            )
            .select_related("question__competition")
            .order_by("?")
        )
        context_data["city_slug"] = city_slug
        context_data["map_city_slug"] = "mapa" if city_slug == "praha" else city_slug
        context_data["competition_phase"] = campaign.phase("competition")
        context_data["commute_modes"] = models.CommuteMode.objects.all()
        context_data["today"] = util.today()
        context_data["num_columns"] = 3 if campaign.recreational else 2
        return context_data


class RidesDetailsView(
    LoginRequiredMixin,
    RegistrationCompleteMixin,
    TitleViewMixin,
    RegistrationMessagesMixin,
    TemplateView,
):
    title = _("Podrobný přehled jízd")
    template_name = "dpnk/rides_details.html"
    registration_phase = "profile_view"

    def get_context_data(self, *args, **kwargs):
        trips, uncreated_trips = self.user_attendance.get_all_trips(util.today())
        uncreated_trips = [
            {
                "date": trip[0],
                "get_direction_display": models.Trip.DIRECTIONS_DICT[trip[1]],
                "get_commute_mode_display": _("Jinak")
                if util.working_day(trip[0])
                else _("Žádná cesta"),
                "distance": None,
                "direction": trip[1],
                "active": self.user_attendance.campaign.day_active(trip[0]),
            }
            for trip in uncreated_trips
        ]
        trips = list(trips) + uncreated_trips
        trips = sorted(
            trips,
            key=lambda trip: trip.direction
            if type(trip) == Trip
            else trip["get_direction_display"],
            reverse=True,
        )
        trips = sorted(
            trips, key=lambda trip: trip.date if type(trip) == Trip else trip["date"]
        )

        context_data = super().get_context_data(*args, **kwargs)
        context_data["trips"] = trips
        days = list(
            util.days(self.user_attendance.campaign.phase("competition"), util.today())
        )
        context_data["other_trips"] = models.Trip.objects.filter(
            user_attendance=self.user_attendance
        ).exclude(date__in=days)
        return context_data


class CalendarView(
    LoginRequiredMixin,
    RegistrationCompleteMixin,
    TitleViewMixin,
    RegistrationMessagesMixin,
    TemplateView,
):
    title = _("Zapište svou jízdu do kalendáře")
    template_name = "dpnk/calendar.html"
    registration_phase = "profile_view"

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        competition = self.user_attendance.campaign.phase("competition")
        entry_enabled_phase = self.user_attendance.campaign.phase("entry_enabled")
        possible_vacation_days_set = set(
            self.user_attendance.campaign.possible_vacation_days()
        )
        active_days_set = set(util.days_active(competition))
        locked_days_set = (
            set(set(util.days(competition)) - active_days_set)
            - possible_vacation_days_set
        )
        context_data.update(
            {
                "possible_vacation_days": json.dumps(
                    [str(day) for day in possible_vacation_days_set]
                ),
                "active_days": json.dumps([str(day) for day in active_days_set]),
                "locked_days": json.dumps([str(day) for day in locked_days_set]),
                "non_working_days": json.dumps(
                    [
                        str(day)
                        for day in util.non_working_days(
                            competition, competition.date_to
                        )
                    ]
                ),
                "events": json.dumps(calendar.get_events(self.request)),
                "commute_modes": models.CommuteMode.objects.all(),
                "entry_enabled_phase": entry_enabled_phase,
                "competition_phase": competition,
                "interactive_entry_enabled": competition.has_started()
                and entry_enabled_phase.is_actual(),
                "leaflet_config": settings.LEAFLET_CONFIG,
            }
        )
        return context_data

    def post(self, request, *args, **kwargs):
        on_vacation = request.POST.get("on_vacation", False)
        on_vacation = on_vacation == "true"
        start_date = util.parse_date(request.POST.get("start_date", None))
        end_date = util.parse_date(request.POST.get("end_date", None))
        possible_vacation_days = self.user_attendance.campaign.possible_vacation_days()
        if not start_date <= end_date:
            raise exceptions.TemplatePermissionDenied(
                _("Data musí být seřazena chronologicky")
            )
        if not {start_date, end_date}.issubset(possible_vacation_days):
            raise exceptions.TemplatePermissionDenied(
                _("Není povoleno editovat toto datum")
            )
        existing_trips = Trip.objects.filter(
            user_attendance=self.user_attendance,
            date__gte=start_date,
            date__lte=end_date,
        )
        no_work = models.CommuteMode.objects.get(slug="no_work")
        updated_trips = []
        if on_vacation:
            for date in util.daterange(start_date, end_date):
                for direction in ["trip_to", "trip_from"]:
                    updated_trips.append(
                        Trip.objects.update_or_create(
                            user_attendance=self.user_attendance,
                            date=date,
                            direction=direction,
                            defaults={"commute_mode": no_work},
                        ),
                    )
        else:
            existing_trips.delete()
        existing_trips = [TripSerializer(trip).data for trip in existing_trips]
        return HttpResponse(json.dumps(existing_trips))


def view_edit_trip(request, date, direction):
    incomplete = registration_complete_gate(request.user_attendance)
    if incomplete is not None:
        return incomplete
    parse_error = False
    try:
        date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        parse_error = True
    if parse_error:
        raise exceptions.TemplatePermissionDenied(
            _("Nemůžete editovat cesty ke starším datům.")
        )
    if direction not in ["trip_to", "trip_from", "recreational"]:
        raise exceptions.TemplatePermissionDenied(_("Neplatný směr cesty."))
    if not request.user_attendance.campaign.day_active(date):
        return TripView.as_view()(request, date=date, direction=direction)
    if models.Trip.objects.filter(
        user_attendance=request.user_attendance, date=date, direction=direction
    ).exists():
        return UpdateTripView.as_view()(request, date=date, direction=direction)
    else:
        return CreateTripView.as_view()(request, date=date, direction=direction)


class EditTripView(
    TitleViewMixin,
    UserAttendanceParameterMixin,
    SuccessMessageMixin,
    LoginRequiredMixin,
):
    form_class = forms.TrackTripForm
    model = models.Trip
    template_name = "dpnk/trip.html"
    title = _("Zadat trasu")

    def get_initial(self, initial=None):
        if initial is None:
            initial = {}
        initial["origin"] = self.request.META.get(
            "HTTP_REFERER", reverse_lazy("profil")
        )
        initial["user_attendance"] = self.user_attendance
        return initial

    def form_valid(self, form):
        self.success_url = form.data["origin"]
        return super().form_valid(form)


class WithTripMixin:
    def get_object(self, queryset=None):
        return get_object_or_404(
            models.Trip,
            user_attendance=self.request.user_attendance,
            direction=self.kwargs["direction"],
            date=self.kwargs["date"],
        )


class UpdateTripView(EditTripView, WithTripMixin, UpdateView):
    pass


class CreateTripView(EditTripView, CreateView):
    def get_initial(self):
        initial = {
            "direction": self.kwargs["direction"],
            "date": self.kwargs["date"],
        }
        return super().get_initial(initial)


class TripView(TitleViewMixin, LoginRequiredMixin, WithTripMixin, TemplateView):
    template_name = "dpnk/view_trip.html"
    title = _("Prohlédnout trasu")

    def get_context_data(self, *args, **kwargs):
        trip = self.get_object()
        context = {
            "title": self.title,
            "days_active": trip.user_attendance.campaign.days_active,
            "active": trip.user_attendance.campaign.day_active(trip.date),
        }
        context["trip"] = trip
        return context


class TripGeoJsonView(LoginRequiredMixin, WithTripMixin, View):
    def get(self, *args, **kwargs):
        geom = self.request.GET.get("geom", "MultiLineString")
        if self.get_object().track:
            if geom == "MultiLineString":
                track_json = self.get_object().track.geojson
            if geom == "LineStrings":
                linestrings = []
                for ls in self.get_object().track:
                    linestrings.append(ls.geojson)
                    track_json = "[" + ",".join(linestrings) + "]"
        else:
            track_json = {}
        return HttpResponse(track_json)


class ThirdPartyRoutesView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        """
        Return a list of routes pulled from third party services.
        """
        from stravasync.tasks import get_activities_as_rest_trips
        from stravasync.models import StravaAccount

        try:
            stravaaccount = StravaAccount.objects.get(user=request.user)
            return JsonResponse({"routes": get_activities_as_rest_trips(stravaaccount)})
        except StravaAccount.DoesNotExist:
            return JsonResponse({"routes": []})
