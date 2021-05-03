from author.decorators import with_author

from django.db import models
from django.db.models import F, Q
from django.utils.translation import ugettext_lazy as _

from dpnk import util


@with_author
class MotivationMessage(models.Model):
    """Motivační hláška"""

    class Meta:
        verbose_name = _("Motivační hláška")
        verbose_name_plural = _("Motivační hlášky")

    campaign_types = models.ManyToManyField(
        "dpnk.CampaignType",
        null=True,
        blank=True,
    )
    message = models.TextField(
        verbose_name=_("Hláška"),
        null=False,
        blank=False,
    )
    note = models.CharField(
        verbose_name=_("Poznámka"),
        max_length=255,
        null=True,
        blank=True,
    )
    frequency_min = models.PositiveIntegerField(
        verbose_name=_("Min pravidelnost"),
        null=True,
        blank=True,
    )
    frequency_max = models.PositiveIntegerField(
        verbose_name=_("Max pravidelnost"),
        null=True,
        blank=True,
    )
    day_from = models.IntegerField(
        verbose_name=_("Ode dne"),
        help_text=_(
            "Počet dní od začátku soutěžní fáze kampaně. Možno zadat i záporné hodnoty pro období před kampaní."
        ),
        null=True,
        blank=True,
    )
    day_to = models.IntegerField(
        verbose_name=_("Do dne"),
        help_text=_(
            "Počet dní od začátku soutěžní fáze kampaně. Možno zadat i záporné hodnoty pro období před kampaní."
        ),
        null=True,
        blank=True,
    )
    team_rank_from = models.PositiveIntegerField(
        verbose_name=_("Od pořadí v týmu"),
        null=True,
        blank=True,
    )
    team_rank_to = models.PositiveIntegerField(
        verbose_name=_("Do pořadí v týmu"),
        null=True,
        blank=True,
    )
    team_backwards_rank_from = models.PositiveIntegerField(
        verbose_name=_("Od pořadí v týmu od konce"),
        null=True,
        blank=True,
    )
    team_backwards_rank_to = models.PositiveIntegerField(
        verbose_name=_("Do pořadí v týmu od konce"),
        null=True,
        blank=True,
    )
    date_from = models.DateField(
        verbose_name=_("Datum od"),
        null=True,
        blank=True,
    )
    date_to = models.DateField(
        verbose_name=_("Datum do"),
        null=True,
        blank=True,
    )
    enabled = models.BooleanField(
        verbose_name=_("Povoleno"),
        default=True,
    )
    priority = models.IntegerField(
        verbose_name=_("Priorita"),
        help_text=_(
            "Priorita hlášky. Zobrazuje se vždy náhodná hláška z těch, které mají nejvyšší prioritu splňují ostatní podmínky."
            "Možno nastavit záporě pro hlášky které mají mít zobrazovat jen pokud není žádní lepší k dispozici."
        ),
        null=False,
        blank=False,
        default=0,
    )

    def __str__(self):
        return "Message %s: %s" % (self.message, self.id)

    @classmethod
    def _get_all_messages(cls, user_attendance):
        queryset = MotivationMessage.objects.filter(enabled=True)

        today = util.today()
        queryset = queryset.filter(Q(date_from__isnull=True) | Q(date_from__lte=today))
        queryset = queryset.filter(Q(date_to__isnull=True) | Q(date_to__gte=today))

        campaign_type = user_attendance.campaign.campaign_type
        queryset = queryset.filter(
            Q(campaign_types__isnull=True) | Q(campaign_types=campaign_type)
        )

        percentage = user_attendance.get_frequency_percentage()
        queryset = queryset.filter(
            Q(frequency_min__isnull=True) | Q(frequency_min__lte=percentage)
        )
        queryset = queryset.filter(
            Q(frequency_max__isnull=True) | Q(frequency_max__gte=percentage)
        )

        days = (today - user_attendance.campaign.competition_phase().date_from).days
        queryset = queryset.filter(Q(day_from__isnull=True) | Q(day_from__lte=days))
        queryset = queryset.filter(Q(day_to__isnull=True) | Q(day_to__gte=days))

        team_rank = user_attendance.get_frequency_rank_in_team()
        queryset = queryset.filter(
            Q(team_rank_from__isnull=True) | Q(team_rank_from__lte=team_rank)
        )
        queryset = queryset.filter(
            Q(team_rank_to__isnull=True) | Q(team_rank_to__gte=team_rank)
        )

        team_backwards_rank = (
            user_attendance.team.members.count()
            - user_attendance.get_frequency_rank_in_team()
            + 1
        )
        queryset = queryset.filter(
            Q(team_backwards_rank_from__isnull=True)
            | Q(team_backwards_rank_from__lte=team_backwards_rank)
        )
        queryset = queryset.filter(
            Q(team_backwards_rank_to__isnull=True)
            | Q(team_backwards_rank_to__gte=team_backwards_rank)
        )
        return queryset.order_by(F("priority").desc(nulls_last=True), "?")

    @classmethod
    def get_random_message(cls, user_attendance):
        messages = MotivationMessage._get_all_messages(user_attendance)
        message = messages.first()
        return message
