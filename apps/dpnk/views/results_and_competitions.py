import collections
import json
import logging

# Django imports
from braces.views import LoginRequiredMixin

from django.conf import settings
from django.core.cache import cache
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import cache_control, cache_page, never_cache
from django.views.generic.base import TemplateView

# Local imports
from .team import OtherTeamMembers
from .. import draw
from .. import forms
from .. import models
from .. import results
from .. import util
from ..models import (
    Answer,
    Campaign,
    City,
    Company,
    Competition,
    Question,
    Subsidiary,
    Trip,
    UserAttendance,
)
from ..models.trip import distance_all_modes
from ..views_mixins import (
    CampaignFormKwargsMixin,
    TitleViewMixin,
    UserAttendanceViewMixin,
)

logger = logging.getLogger(__name__)


class DiplomasView(
    TitleViewMixin, UserAttendanceViewMixin, LoginRequiredMixin, TemplateView
):
    title = _("Vaše diplomy a výsledky v minulých ročnících")
    template_name = "dpnk/diplomas.html"
    registration_phase = "profile_view"

    def get_context_data(self, *args, **kwargs):
        user_attendances = (
            self.user_attendance.userprofile.userattendance_set.all().order_by("-id")
        )
        teams = []
        for ua in self.user_attendance.userprofile.userattendance_set.all():
            if ua.team and ua.team.name:
                teams.append(ua.team)
        context_data = super().get_context_data(*args, **kwargs)
        context_data["user_attendances"] = user_attendances
        context_data["teams"] = teams
        return context_data


class FrequencyView(OtherTeamMembers):
    template_name = "dpnk/frequency.html"
    title = _("Pravidelnost")

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        context_data["approved_team_members"] = self.user_attendance.team.members
        return context_data


class CompetitionsRulesView(CampaignFormKwargsMixin, TitleViewMixin, TemplateView):
    title_base = _("Pravidla soutěží")

    def get_title(self, *args, **kwargs):
        city = get_object_or_404(City, slug=kwargs["city_slug"])
        return "%s - %s" % (self.title_base, city)

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        city_slug = kwargs["city_slug"]
        competitions = Competition.objects.filter(
            Q(city__slug=city_slug) | Q(city__isnull=True, company=None),
            campaign=self.campaign,
            is_public=True,
        )
        context_data["competitions"] = competitions
        context_data["city_slug"] = city_slug
        context_data["campaign_slug"] = self.campaign.slug
        return context_data


class AdmissionsView(
    UserAttendanceViewMixin, TitleViewMixin, LoginRequiredMixin, TemplateView
):
    title = _("Výsledky soutěží")
    success_url = reverse_lazy("competitions")
    competition_types = None

    @method_decorator(never_cache)
    @method_decorator(cache_control(max_age=0, no_cache=True, no_store=True))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        context_data["competitions"] = self.user_attendance.get_competitions(
            competition_types=self.competition_types
        )
        context_data["registration_phase"] = "competitions"
        return context_data

    # This is here for NewRelic to distinguish from TemplateView.get
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class LengthCompetitionsView(AdmissionsView):
    title = _("Výsledky výkonnostních soutěží")
    competition_types = ("length",)
    template_name = "dpnk/competitions.html"


class FrequencyCompetitionsView(AdmissionsView):
    title = _("Výsledky pravidelnostních soutěží")
    competition_types = ("frequency",)
    template_name = "dpnk/competitions.html"


class QuestionareCompetitionsView(AdmissionsView):
    title = _("Výsledky dotazníkových soutěží a soutěží na kreativitu")
    competition_types = ("questionnaire",)
    template_name = "dpnk/competitions.html"


class CompetitionResultsView(TitleViewMixin, TemplateView):
    template_name = "dpnk/competition_results.html"
    title = _("Výsledky soutěže")

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        competition_slug = kwargs.get("competition_slug")

        try:
            context_data["competition"] = Competition.objects.get(slug=competition_slug)
        except Competition.DoesNotExist:
            logger.info(
                "Unknown competition",
                extra={"slug": competition_slug, "request": self.request},
            )
            return {
                "fullpage_error_message": mark_safe(
                    _(
                        "Tuto soutěž v systému nemáme. Pokud si myslíte, že by zde měly být výsledky nějaké soutěže, napište prosím na "
                        '<a href="mailto:kontakt@dopracenakole.cz?subject=Neexistující soutěž">kontakt@dopracenakole.cz</a>'
                    ),
                ),
                "title": _("Není vybraný tým"),
            }
        return context_data

    # This is here for NewRelic to distinguish from TemplateView.get
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class QuestionnaireView(TitleViewMixin, LoginRequiredMixin, TemplateView):
    template_name = "dpnk/questionaire.html"
    success_url = reverse_lazy("profil")
    title = _("Vyplňte odpovědi")
    form_class = forms.AnswerForm

    def dispatch(self, request, *args, **kwargs):
        questionaire_slug = kwargs["questionnaire_slug"]
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        self.user_attendance = request.user_attendance
        self.userprofile = request.user.userprofile
        try:
            self.competition = Competition.objects.get(slug=questionaire_slug)
        except Competition.DoesNotExist:
            logger.exception(
                "Unknown questionaire",
                extra={"slug": questionaire_slug, "request": request},
            )
            return HttpResponse(
                _(
                    '<div class="text-danger">Tento dotazník v systému nemáme.'
                    " Pokud si myslíte, že by zde mělo jít vyplnit dotazník, napište prosím na"
                    ' <a href="mailto:{contact_email}?subject=Neexistující dotazník">{contact_email}</a></div>'
                ).format(contact_email=request.user_attendance.campaign.contact_email),
                status=401,
            )
        self.show_points = (
            self.competition.has_finished() or self.userprofile.user.is_superuser
        )
        self.is_actual = self.competition.is_actual()
        self.questions = Question.objects.filter(competition=self.competition).order_by(
            "order"
        )

        for question in self.questions:
            try:
                answer = question.answer_set.get(user_attendance=self.user_attendance)
                question.points_given = answer.points_given
                question.comment_given = answer.comment_given
            except Answer.DoesNotExist:
                answer = Answer(question=question, user_attendance=self.user_attendance)
            question.form = self.form_class(
                instance=answer,
                question=question,
                prefix="question-%s" % question.pk,
                show_points=self.show_points,
                is_actual=self.is_actual,
            )
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data())

    def post(self, request, *args, **kwargs):
        if not self.is_actual:
            return HttpResponse(
                format_html(
                    "<div class='text-warning'>{}</div>",
                    _("Soutěž již nelze vyplňovat"),
                )
            )

        invalid_count = 0
        for question in self.questions:
            if not question.with_answer():
                continue

            try:
                answer = question.answer_set.get(user_attendance=self.user_attendance)
                question.points_given = answer.points_given
            except Answer.DoesNotExist:
                answer = Answer(question=question, user_attendance=self.user_attendance)
            question.points_given = answer.points_given
            question.form = self.form_class(
                request.POST,
                files=request.FILES,
                instance=answer,
                question=question,
                prefix="question-%s" % question.pk,
                show_points=self.show_points,
                is_actual=self.is_actual,
            )
            if not question.form.is_valid():
                invalid_count += 1

        if invalid_count == 0:
            for question in self.questions:
                if not question.with_answer():
                    continue
                question.form.save()
            # TODO: use Celery for this
            results.recalculate_result_competitor(self.user_attendance)
            messages.add_message(
                request, messages.SUCCESS, _("Odpovědi byly úspěšně zadány")
            )
            return redirect(self.success_url)
        context_data = self.get_context_data()
        context_data["invalid_count"] = invalid_count
        return render(request, self.template_name, context_data)

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)

        context_data.update(
            {
                "questions": self.questions,
                "questionaire": self.competition,
                "show_submit": self.is_actual,
                "show_points": self.show_points,
            }
        )
        return context_data


class QuestionnaireAnswersAllView(TitleViewMixin, TemplateView):
    template_name = "dpnk/questionnaire_answers_all.html"
    title = _("Výsledky všech soutěží")

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)

        competition_slug = kwargs.get("competition_slug")
        competition = Competition.objects.get(slug=competition_slug)
        if (
            not competition.public_answers
            and not self.request.user.is_superuser
            and self.request.user.userprofile.competition_edition_allowed(competition)
        ):
            context_data["fullpage_error_message"] = _(
                "Tato soutěž nemá povolené prohlížení odpovědí."
            )
            context_data["title"] = _("Odpovědi nejsou dostupné")
            return context_data

        competitors = competition.get_results()
        competitors = competitors.select_related(
            "user_attendance__team__subsidiary__city",
            "user_attendance__userprofile__user",
        )

        for competitor in competitors:
            competitor.answers = Answer.objects.filter(
                user_attendance__in=competitor.user_attendances(),
                question__competition__slug=competition_slug,
            ).select_related("question")
        context_data["show_points"] = competition.has_finished() or (
            self.request.user.is_authenticated
            and self.request.user.userprofile.user.is_superuser
        )
        context_data["competitors"] = competitors
        context_data["competition"] = competition
        return context_data


@staff_member_required
def questions(request):
    questions = Question.objects.all()
    if not request.user.is_superuser:
        questions = questions.filter(
            competition__city__in=request.user.userprofile.administrated_cities.all()
        )
    questions = questions.filter(competition__campaign__slug=request.subdomain)
    questions = questions.order_by(
        "-competition__campaign", "competition__slug", "order"
    )
    questions = questions.distinct()
    questions = questions.select_related("competition__campaign", "choice_type")
    questions = questions.prefetch_related("answer_set", "competition__city")
    return render(
        request,
        "admin/questions.html",
        {
            "title": _("Otázky v dotaznících"),
            "questions": questions,
        },
    )


@staff_member_required
def questionnaire_results(
    request,
    competition_slug=None,
):
    competition = Competition.objects.get(slug=competition_slug)
    if (
        not request.user.is_superuser
        and request.user.userprofile.competition_edition_allowed(competition)
    ):
        return HttpResponse(
            format_html(
                "<div class='text-warning'>{}</div>",
                _("Soutěž je vypsána ve městě, pro které nemáte oprávnění."),
            )
        )

    competitors = competition.get_results()
    return render(
        request,
        "admin/questionnaire_results.html",
        {
            "competition_slug": competition_slug,
            "competitors": competitors,
            "competition": competition,
            "title": _("Výsledky odpovědí na dotazník"),
        },
    )


@staff_member_required
def questionnaire_answers(
    request,
    competition_slug=None,
):
    competition = Competition.objects.get(slug=competition_slug)
    if (
        not request.user.is_superuser
        and request.user.userprofile.competition_edition_allowed(competition)
    ):
        return HttpResponse(
            format_html(
                "<div class='text-warning'>{}</div>",
                _("Soutěž je vypsána ve městě, pro které nemáte oprávnění."),
            )
        )

    try:
        competitor_result = competition.get_results().get(pk=request.GET["uid"])
    except models.CompetitionResult.DoesNotExist:
        return HttpResponse(
            _('<div class="text-danger">Nesprávně zadaný soutěžící.</div>'), status=401
        )
    answers = Answer.objects.filter(
        user_attendance__in=competitor_result.user_attendances(),
        question__competition__slug=competition_slug,
    )
    total_points = competitor_result.result
    return render(
        request,
        "admin/questionnaire_answers.html",
        {
            "answers": answers,
            "competitor": competitor_result,
            "media": settings.MEDIA_URL,
            "title": _("Odpovědi na dotazník"),
            "total_points": total_points,
        },
    )


@staff_member_required  # noqa
def answers(request):
    question_id = request.GET["question"]
    question = Question.objects.get(id=question_id)
    if (
        not request.user.is_superuser
        and request.user.userprofile.competition_edition_allowed(question.competition)
    ):
        return HttpResponse(
            format_html(
                "<div class='text-warning'>{}</div>",
                _("Otázka je položená ve městě, pro které nemáte oprávnění."),
            ),
            status=401,
        )

    if request.method == "POST":
        points = [
            (k.split("-")[1], v)
            for k, v in request.POST.items()
            if k.startswith("points-")
        ]
        for p in points:
            if not p[1] in ("", "None", None):
                answer = Answer.objects.get(id=p[0])
                try:
                    answer.points_given = float(p[1].replace(",", "."))
                except ValueError:
                    answer.points_given = None

                answer.save()

    answers = Answer.objects.filter(question_id=question_id).order_by("-points_given")
    answers = answers.select_related(
        "user_attendance__team__subsidiary__city", "user_attendance__userprofile__user"
    )
    answers = answers.prefetch_related("choices")
    total_respondents = answers.count()
    count = {c: {} for c in City.objects.all()}
    count_all = {}
    respondents = {c: 0 for c in City.objects.all()}
    choice_names = {}

    for a in answers:
        a.city = (
            a.user_attendance.team.subsidiary.city
            if a.user_attendance and a.user_attendance.team
            else None
        )

    if question.question_type in ("choice", "multiple-choice"):
        for a in answers:
            if a.city:
                respondents[a.city] += 1
                for c in a.choices.all():
                    try:
                        count[a.city][c.id] += 1
                    except KeyError:
                        count[a.city][c.id] = 1
                        choice_names[c.id] = c.text
                    try:
                        count_all[c.id] += 1
                    except KeyError:
                        count_all[c.id] = 1

    stat = {c: [] for c in City.objects.all()}
    stat["Celkem"] = []
    for city, city_count in count.items():
        for k, v in city_count.items():
            stat[city].append((choice_names[k], v, float(v) / respondents[city] * 100))
    for k, v in count_all.items():
        stat["Celkem"].append((choice_names[k], v, float(v) / total_respondents * 100))

    def get_percentage(r):
        return r[2]

    for k in stat.keys():
        stat[k].sort(key=get_percentage, reverse=True)

    return render(
        request,
        "admin/answers.html",
        {
            "question": question,
            "answers": answers,
            "stat": stat,
            "total_respondents": total_respondents,
            "media": settings.MEDIA_URL,
            "title": _("Odpověd na dotazník"),
            "choice_names": choice_names,
        },
    )


def distance(trips):
    return distance_all_modes(trips)["distance__sum"] or 0


def total_distance(campaign):
    return distance_all_modes(Trip.objects.filter(user_attendance__campaign=campaign))


def period_distance(campaign, day_from, day_to):
    return distance_all_modes(
        Trip.objects.filter(
            user_attendance__campaign=campaign, date__gte=day_from, date__lte=day_to
        )
    )


def trips(trips):
    return trips.count()


@cache_page(60 * 60)
def statistics(
    request,
    template="dpnk/statistics.html",
):
    campaign_slug = request.subdomain
    campaign = Campaign.objects.get(slug=campaign_slug)
    distances = total_distance(campaign)
    distances_today = period_distance(campaign, util.today(), util.today())
    variables = {}
    variables["ujeta-vzdalenost"] = distances["distance__sum"] or 0
    variables["usetrene-emise-co2"] = util.get_emissions(
        distances["distance__sum"] or 0
    )["co2"]
    variables["ujeta-vzdalenost-kolo"] = distances["distance_bicycle"]
    variables["ujeta-vzdalenost-pesky"] = distances["distance_foot"]
    variables["ujeta-vzdalenost-dnes"] = distances_today["distance__sum"]
    variables["pocet-cest"] = distances["count__sum"] or 0
    variables["pocet-cest-pesky"] = distances["count_foot"]
    variables["pocet-cest-kolo"] = distances["count_bicycle"]
    variables["pocet-cest-dnes"] = distances_today["count__sum"]
    variables["pocet-zaplacenych"] = (
        UserAttendance.objects.filter(
            Q(campaign=campaign) & Q(payment_status="done"),
        )
        .exclude(Q(transactions__payment__pay_type__in=models.Payment.NOT_PAYING_TYPES))
        .distinct()
        .count()
    )
    variables["pocet-prihlasenych"] = (
        UserAttendance.objects.filter(campaign=campaign).distinct().count()
    )
    variables["pocet-soutezicich"] = (
        UserAttendance.objects.filter(
            Q(campaign=campaign) & Q(payment_status="done"),
        )
        .distinct()
        .count()
    )
    variables["pocet-spolecnosti"] = (
        Company.objects.filter(Q(subsidiaries__teams__campaign=campaign))
        .distinct()
        .count()
    )
    variables["pocet-pobocek"] = (
        Subsidiary.objects.filter(Q(teams__campaign=campaign)).distinct().count()
    )

    data = json.dumps(variables)
    return HttpResponse(data)


@cache_page(60 * 60)
def daily_chart(
    request,
    template="dpnk/daily-chart.html",
):
    campaign_slug = request.subdomain
    campaign = Campaign.objects.get(slug=campaign_slug)
    values = [
        period_distance(campaign, day, day)["distance__sum"] or 0
        for day in util.days(campaign.phase("competition"))
    ]
    return render(
        request,
        template,
        {
            "values": values,
            "days": reversed(list(util.days(campaign.phase("competition")))),
            "max_value": max(values),
        },
    )


@cache_page(60 * 60)
def daily_distance_extra_json(
    request,
):
    campaign_slug = request.subdomain
    campaign = Campaign.objects.get(slug=campaign_slug)
    values = collections.OrderedDict()
    for day in util.days(campaign.phase("competition")):
        distances = period_distance(campaign, day, day)
        emissions_co2 = util.get_emissions(distances["distance__sum"] or 0)["co2"]
        values[str(day)] = {
            "distance": distances["distance__sum"] or 0,
            "distance_bicycle": distances["distance_bicycle"] or 0,
            "distance_foot": distances["distance_foot"] or 0,
            "emissions_co2": emissions_co2,
        }
    data = json.dumps(values)
    return HttpResponse(data)


class CompetitorCountView(TitleViewMixin, TemplateView):
    template_name = "dpnk/competitor_count.html"
    title = _("Počty soutěžících")

    @method_decorator(cache_page(60 * 60 - 4))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        campaign_slug = self.request.subdomain
        context_data["campaign_slug"] = campaign_slug
        context_data["cities"] = models.CityInCampaign.objects.filter(
            campaign__slug=campaign_slug
        )
        context_data["without_city"] = UserAttendance.objects.filter(
            payment_status__in=("done", "no_admission"),
            campaign__slug=campaign_slug,
            team=None,
        )
        context_data["total"] = UserAttendance.objects.filter(
            payment_status__in=("done", "no_admission"), campaign__slug=campaign_slug
        )
        competition_phase = self.request.campaign.competition_phase()
        context_data["total_distances"] = distance_all_modes(
            models.Trip.objects.filter(
                date__range=[competition_phase.date_from, competition_phase.date_to],
                user_attendance__payment_status__in=("done", "no_admission"),
                user_attendance__campaign__slug=campaign_slug,
            ),
        )
        context_data["total_emissions"] = util.get_emissions(
            context_data["total_distances"]["distance__sum"]
        )
        return context_data


class DrawResultsView(LoginRequiredMixin, TitleViewMixin, TemplateView):
    template_name = "admin/draw.html"
    title = _("Losování")
    paginate_by = 20

    def _get_counter_class(self):
        """Get Counter class"""

        class Counter:
            count = 0

            def increment(self):
                self.count += 1
                return ""

        return Counter

    def _handle_cache(self, competition_slug, timeout=3600):
        """Handle cache

        :param str competition_slug: competition slug
        :param int timeout: cache timeout with default value 1200 seconds

        :return str draw_results: list of CompetitionResult model instances
        """
        draw_results_competition_slug = cache.get(competition_slug)
        if (
            not draw_results_competition_slug
            or draw_results_competition_slug != competition_slug
        ):
            draw_results = draw.draw(competition_slug)
            cache.set_many(
                {
                    f"{competition_slug}-results": draw_results,
                    competition_slug: competition_slug,
                },
                timeout=timeout,
            )
        elif draw_results_competition_slug:
            draw_results = cache.get(f"{competition_slug}-results")
            if not draw_results:
                draw_results = draw.draw(competition_slug)
                cache.set_many(
                    {
                        f"{competition_slug}-results": draw_results,
                        competition_slug: competition_slug,
                    },
                    timeout=timeout,
                )
        return draw_results

    def get_context_data(self, city_slug=None, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        competition_slug = kwargs.get("competition_slug")
        Counter = self._get_counter_class()
        # Paginator
        paginator = Paginator(
            self._handle_cache(competition_slug),
            self.paginate_by,
        )
        page = self.request.GET.get("page", 1)
        Counter.count = int(page) * self.paginate_by - self.paginate_by
        page_obj = paginator.page(page)
        # Context data
        context_data["results"] = page_obj
        context_data["page"] = Counter()
        return context_data
