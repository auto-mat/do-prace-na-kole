# -*- coding: utf-8 -*-

# Author: Hynek Hanke <hynek.hanke@auto-mat.cz>
# Author: Petr Dlouhý <petr.dlouhy@email.cz>
#
# Copyright (C) 2016 o.s. Auto*Mat
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
import logging
import re

from coupons.models import DiscountCoupon

from denorm import denormalized, depend_on_related

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db import models
from django.contrib.humanize.templatetags.humanize import intcomma
from django.contrib.sites.models import Site
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db.models import Q, F, Sum
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.utils.translation import activate, get_language
from django.utils.translation import ugettext_lazy as _

from motivation_messages.models import MotivationMessage

from notifications.signals import notify, revoke_notification

from stale_notifications.model_mixins import StaleSyncMixin

from .company_admin import CompanyAdmin
from .diploma import Diploma
from .landingpageicon import LandingPageIcon
from .phase import Phase
from .transactions import Payment, Transaction
from .trip import Trip
from .util import MAP_DESCRIPTION
from .. import mailing, util

# from ..email import register_mail

logger = logging.getLogger(__name__)


class UserAttendance(StaleSyncMixin, models.Model):
    """Účast uživatele v kampani"""

    last_sync_string = _("Poslední odeslání notifikačního e-mailu")

    class Meta:
        verbose_name = _("Účastník kampaně")
        verbose_name_plural = _("Účastníci kampaně")
        unique_together = (("userprofile", "campaign"),)

    TEAMAPPROVAL = (
        ("approved", _("Odsouhlasený")),
        ("undecided", _("Nerozhodnuto")),
        ("denied", _("Zamítnutý")),
    )

    campaign = models.ForeignKey(
        "Campaign",
        verbose_name=_("Kampaň"),
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )
    userprofile = models.ForeignKey(
        "UserProfile",
        verbose_name=_("Uživatelský profil"),
        related_name="userattendance_set",
        unique=False,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )
    distance = models.FloatField(
        verbose_name=_("DEPRECATED"),
        help_text=_("DEPRECATED"),
        default=None,
        blank=True,
        null=True,
    )
    track = models.MultiLineStringField(
        verbose_name=_("DEPRECATED"),
        help_text=MAP_DESCRIPTION,
        srid=4326,
        null=True,
        blank=True,
        geography=True,
    )
    dont_want_insert_track = models.BooleanField(
        verbose_name=_("DEPRECATED"),
        default=False,
        null=False,
    )
    team = models.ForeignKey(
        "Team",
        related_name="users",
        verbose_name=_("Tým"),
        null=True,
        blank=True,
        default=None,
        on_delete=models.SET_NULL,
    )
    approved_for_team = models.CharField(
        verbose_name=_("Souhlas týmu"),
        choices=TEAMAPPROVAL,
        max_length=16,
        null=False,
        default="undecided",
    )
    t_shirt_size = models.ForeignKey(
        "t_shirt_delivery.TShirtSize",
        verbose_name=_("Velikost trika"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    discount_coupon = models.ForeignKey(
        DiscountCoupon,
        verbose_name=_("Slevový kupón"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    discount_coupon_used = models.DateTimeField(
        verbose_name=_("Datum použití slevového kupónu"),
        null=True,
        blank=True,
    )
    created = models.DateTimeField(
        verbose_name=_("Datum vytvoření"),
        auto_now_add=True,
        null=True,
    )
    updated = models.DateTimeField(
        verbose_name=_("Datum poslední změny"),
        auto_now=True,
        null=True,
    )
    personal_data_opt_in = models.BooleanField(
        verbose_name=_("Souhlas se zpracováním osobních údajů."),
        blank=False,
        default=False,
    )

    sandwich_model = Diploma

    def diploma(self):
        try:
            return Diploma.objects.filter(obj=self).first()
        except Diploma.DoesNotExist:
            return None

    def get_diploma_pdf_url(self):
        diploma = self.diploma()
        if diploma:
            if re.match(r"http:|https", settings.MEDIA_URL):
                return diploma.pdf.url
            else:
                return f"{setting.MEDIA_URL}{diploma.pdf.url}"
        return diploma

    def get_sandwich_type(self):
        return self.campaign.sandwich_type

    def payments(self):
        return self.transactions.instance_of(Payment)

    def first_name(self):
        return self.userprofile.user.first_name

    def last_name(self):
        return self.userprofile.user.last_name

    def name(self, cs_vokativ=False):
        return self.userprofile.name(cs_vokativ=cs_vokativ)

    name.admin_order_field = "userprofile__user__last_name"
    name.short_description = _("Jméno")

    def name_for_trusted(self):
        return self.userprofile.name_for_trusted()

    name_for_trusted.admin_order_field = "userprofile__user__last_name"
    name_for_trusted.short_description = _("Jméno")

    def __str__(self):
        return self.userprofile.name()

    def t_shirt_price(self):
        if self.t_shirt_size:
            return self.t_shirt_size.price
        else:
            return 0

    def discount_multiplier(self):
        if self.discount_coupon:
            return self.discount_coupon.discount_multiplier()
        else:
            return 1

    def admission_fee_for_category(self, category):
        price_level = self.campaign.get_current_price_level(
            date_time=util.today(), category=category
        )
        if price_level:
            base_price = price_level.price
        else:
            base_price = 0
        return (base_price + self.t_shirt_price()) * self.discount_multiplier()

    def admission_fee(self):
        return self.admission_fee_for_category("basic")

    def has_admission_fee(self):
        return (
            self.campaign.get_current_price_level(
                date_time=util.today(), category="basic"
            )
            is not None
            or self.campaign.get_current_price_level(
                date_time=util.today(), category="company"
            )
            is not None
            or self.campaign.get_current_price_level(
                date_time=util.today(), category="school"
            )
            is not None
        )

    def beneficiary_admission_fee(self):
        return self.campaign.benefitial_admission_fee + self.t_shirt_price()

    def company_admission_fee(self):
        return self.admission_fee_for_category("company")

    def company_admission_fee_intcomma(self):
        return intcomma(self.company_admission_fee())

    @denormalized(
        models.ForeignKey,
        to="Payment",
        null=True,
        on_delete=models.SET_NULL,
        skip={"updated", "created", "last_sync_time"},
    )
    @depend_on_related(
        "Payment", foreign_key="payment_user_attendance", skip={"updated", "created"}
    )
    def representative_payment(self):
        if self.team and self.team.subsidiary and not self.has_admission_fee():
            return None

        try:
            return self.payments().filter(status__in=Payment.done_statuses).latest("id")
        except Transaction.DoesNotExist:
            pass

        try:
            return (
                self.payments().filter(status__in=Payment.waiting_statuses).latest("id")
            )
        except Transaction.DoesNotExist:
            pass

        try:
            return self.payments().latest("id")
        except Transaction.DoesNotExist:
            pass

        return None

    PAYMENT_CHOICES = (
        ("no_admission", _("neplatí se")),
        ("none", _("žádné platby")),
        ("done", _("zaplaceno")),
        ("waiting", _("nepotvrzeno")),
        ("unknown", _("neznámý")),
    )

    @denormalized(
        models.CharField,
        choices=PAYMENT_CHOICES,
        max_length=20,
        null=True,
        skip={"updated", "created", "last_sync_time"},
    )
    @depend_on_related(
        "Payment", foreign_key="payment_user_attendance", skip={"updated", "created"}
    )
    def payment_status(self):
        if self.discount_coupon and self.discount_coupon.discount == 100:
            return "done"
        payment = self.representative_payment
        if self.team and self.team.subsidiary and not self.has_admission_fee():
            return "no_admission"
        if self.admission_fee() == 0 and not payment:
            return "done"
        if not payment:
            return "none"
        if payment.status in Payment.done_statuses:
            return "done"
        if payment.status in Payment.waiting_statuses:
            return "waiting"
        return "unknown"

    def payment_class(self):
        payment_classes = {
            "no_admission": "success",
            "none": "error",
            "done": "success",
            "waiting": "warning",
            "unknown": "warning",
        }
        return payment_classes[self.payment_status]

    def payment_type_string(self):
        if self.representative_payment:
            pay_type = self.representative_payment.pay_type
            if pay_type:
                return Payment.PAY_TYPES_DICT[pay_type]
        return _("žádná platba")

    def payment_type(self):
        if self.representative_payment:
            return self.representative_payment.pay_type

    def payment_subject(self):
        company = "company"
        school = "school"
        company_coordinator_pay_type = "fc"
        if self.discount_coupon:
            return "voucher"
        if self.representative_payment:
            if (
                self.representative_payment.pay_type == company_coordinator_pay_type
                and self.representative_payment.pay_subject == company
            ):
                return company
            elif (
                self.representative_payment.pay_type == company_coordinator_pay_type
                and self.representative_payment.pay_subject == school
            ):
                return school
            return "individual"

    def payment_amount(self):
        if self.representative_payment:
            return self.representative_payment.amount

    def payment_category(self):
        if self.representative_payment:
            return self.representative_payment.pay_category

    def get_competitions(self, competition_types=None):
        from .. import results

        return results.get_competitions_with_info(self, competition_types)

    def get_rides_count(self):
        from .. import results

        try:
            return results.get_rides_count(self, self.campaign.phase("competition"))
        except Phase.DoesNotExist:
            return 0

    @denormalized(
        models.IntegerField, null=True, skip={"updated", "created", "last_sync_time"}
    )
    @depend_on_related("Trip", foreign_key="user_attendance")
    def get_rides_count_denorm(self):
        return self.get_rides_count()

    def get_frequency(self, day=None):
        from .. import results

        try:
            return results.get_userprofile_frequency(
                self, self.campaign.phase("competition"), day
            )[2]
        except Phase.DoesNotExist:
            return 0

    @denormalized(
        models.FloatField, null=True, skip={"updated", "created", "last_sync_time"}
    )
    @depend_on_related("Trip", foreign_key="user_attendance")
    def frequency(self):
        return self.get_frequency()

    def get_frequency_percentage(self, day=None):
        if day:
            return self.get_frequency(day) * 100
        else:
            frequency = self.frequency if self.frequency is not None else 0
            return frequency * 100

    def get_frequency_icons(self, frequency):
        roles = {}
        for icon in LandingPageIcon.objects.filter(
            max_frequency__gte=round(frequency), min_frequency__lte=round(frequency)
        ):
            roles[icon.role] = icon.file.url

        return roles

    def get_user_frequency_icons(self):
        frequency = self.get_frequency_percentage()
        return self.get_frequency_icons(frequency)

    def get_team_frequency_icons(self):
        frequency = self.team.get_frequency_percentage()
        return self.get_frequency_icons(frequency)

    @denormalized(
        models.FloatField, null=True, skip={"updated", "created", "last_sync_time"}
    )
    @depend_on_related("Trip", foreign_key="user_attendance")
    def trip_length_total(self):
        """
        Total trip length NOT including recreational trips.
        """
        from .. import results

        try:
            return results.get_userprofile_length(
                [self], self.campaign.phase("competition")
            )
        except Phase.DoesNotExist:
            return 0

    def trip_length_total_rounded(self):
        return round(self.trip_length_total or 0, 2)

    @denormalized(
        models.FloatField, null=True, skip={"updated", "created", "last_sync_time"}
    )
    @depend_on_related("Trip", foreign_key="user_attendance")
    def total_trip_length_including_recreational(self):
        from .. import results

        try:
            return results.get_userprofile_length(
                [self], self.campaign.phase("competition"), recreational=True
            )
        except Phase.DoesNotExist:
            return 0

    def trip_length_total_including_recreational_rounded(self):
        return round(self.total_trip_length_including_recreational, 2)

    @denormalized(
        models.IntegerField, null=True, skip={"updated", "created", "last_sync_time"}
    )
    @depend_on_related("Trip", foreign_key="user_attendance")
    def working_rides_base_count(self):
        """Return number of rides, that should be acomplished to this date"""
        from .. import results

        return results.get_working_trips_count(self, self.campaign.phase("competition"))

    def get_working_rides_base_count(self):
        """Return number of rides, that should be acomplished to this date"""
        if self.working_rides_base_count is not None:
            return self.working_rides_base_count
        else:
            return 0

    def get_remaining_rides_count(self):
        """Return number of rides, that are remaining to the end of competition"""
        competition_phase = self.campaign.competition_phase()
        days_count = util.days_count(competition_phase, competition_phase.date_to)
        days_count_till_now = util.days_count(competition_phase, util.today())
        return (days_count - days_count_till_now).days * 2

    def get_remaining_max_theoretical_frequency_percentage(self):
        """Return maximal frequency that can be achieved till end of the competition"""
        from .. import results

        remaining_rides = self.get_remaining_rides_count()
        rides_count = self.get_rides_count_denorm
        competition_phase = self.campaign.competition_phase()
        working_rides_base = (
            results.get_working_trips_count_without_minimum(self, competition_phase)
            + remaining_rides
        )
        working_rides_count = max(working_rides_base, self.campaign.minimum_rides_base)
        return ((rides_count + remaining_rides) / working_rides_count) * 100

    def get_minimum_rides_base_proportional(self):
        from .. import results

        return results.get_minimum_rides_base_proportional(
            self.campaign.phase("competition"), util.today()
        )

    def get_distance(self, round_digits=2):
        track = self.get_initial_track()
        if track:
            return round(util.get_multilinestring_length(track), round_digits)
        if self.distance:
            return self.distance
        else:
            return 0

    get_distance.short_description = _("Vzdálenost (km) do práce")
    get_distance.admin_order_field = "distance"

    def get_userprofile(self):
        return self.userprofile

    def is_libero(self):
        if (
            self.team
            and self.team_member_count()
            and self.campaign.competitors_choose_team()
        ):
            return self.team_member_count() <= 1
        else:
            return False

    def package_shipped(self):
        from t_shirt_delivery.models import PackageTransaction

        return self.transactions.filter(
            instance_of=PackageTransaction,
            status__in=PackageTransaction.shipped_statuses,
        ).last()

    def other_user_attendances(self, campaign):
        return self.userprofile.userattendance_set.exclude(campaign=campaign)

    def company(self):
        if self.team:
            return self.team.subsidiary.company

        try:
            return self.userprofile.company_admin.get(
                campaign=self.campaign
            ).administrated_company
        except CompanyAdmin.DoesNotExist:
            return None

    def entered_competition_reason(self):
        if not self.userprofile.profile_complete() or not self.personal_data_opt_in:
            return "profile_uncomplete"
        if not self.is_team_approved():
            if self.team_complete():
                return "team_waiting"
            else:
                return "team_uncomplete"
        if not self.tshirt_complete():
            return "tshirt_uncomplete"
        if not self.has_paid():
            if self.payment_complete():
                return "payment_waiting"
            else:
                return "payment_uncomplete"
        return True

    def entered_competition(self):
        return (
            True
            if (
                self.tshirt_complete()
                and self.is_team_approved()
                and self.has_paid()
                and self.userprofile.profile_complete()
                and self.personal_data_opt_in
            )
            else False
        )

    def team_member_count(self):
        if self.team:
            return self.team.member_count

    def tshirt_complete(self):
        return (not self.campaign.has_any_tshirt) or (self.t_shirt_size is not None)

    def team_complete(self):
        return self.team

    def is_team_approved(self):
        return self.team and self.approved_for_team == "approved"

    def payment_complete(self):
        return self.payment_status not in ("none", None)

    def payment_complete_date(self):
        if self.discount_coupon:
            return self.discount_coupon_used
        if self.representative_payment is not None:
            if self.representative_payment.realized:
                return self.representative_payment.realized
            else:
                return self.representative_payment.created
        return self.created

    def has_paid(self):
        return self.payment_status in ("done", "no_admission") or (
            not self.has_admission_fee()
        )

    def get_emissions(self, distance=None):
        return util.get_emissions(self.trip_length_total)

    def get_active_trips(self):
        days = list(util.days_active(self.campaign.phase("competition")))
        return self.get_trips(days)

    def get_all_trips(self, day=None):
        try:
            days = list(util.days(self.campaign.competition_phase(), day))
        except Phase.DoesNotExist:
            days = []
        return self.get_trips(days)

    def eco_trip_count(self):
        return self.get_rides_count_denorm

    def avatar_url(self):
        import avatar.models

        try:
            avatars = avatar.models.Avatar.objects.filter(
                user=self.userprofile.user,
            )
            return avatars[0].get_absolute_url() if avatars.count() >= 1 else ""
        except avatar.models.Avatar.DoesNotExist:
            return ""

    def company_admin_emails(self):
        if self.team:
            return self.team.subsidiary.company.admin_emails(self.campaign)

    def get_trips(self, days):
        """
        Return trips in given days, return days without any trip
        @param days
        @return trips in those days
        @return days without trip
        """
        trips = Trip.objects.filter(user_attendance=self, date__in=days)
        trip_days = trips.values_list("date", "direction")
        expected_trip_days = [
            (day, direction)
            for day in days
            for direction in self.campaign.get_directions()
        ]
        uncreated_trips = sorted(set(expected_trip_days) - set(trip_days))
        return trips, uncreated_trips

    def get_initial_track(self):
        trips, _ = self.get_all_trips()
        previous_trip_with_track = (
            trips.filter(track__isnull=False).order_by("-date", "-direction").first()
        )
        if previous_trip_with_track:
            return previous_trip_with_track.track
        if self.track:
            return self.track
        return None

    @denormalized(
        models.ForeignKey,
        to="CompanyAdmin",
        null=True,
        on_delete=models.SET_NULL,
        skip={"updated", "created", "last_sync_time"},
    )
    @depend_on_related("UserProfile", skip={"mailing_hash"})
    def related_company_admin(self):
        """Get company coordinator profile for this user attendance"""
        try:
            return CompanyAdmin.objects.get(
                userprofile=self.userprofile, campaign=self.campaign
            )
        except CompanyAdmin.DoesNotExist:
            return None

    def unanswered_questionnaires(self):
        from .. import results

        return results.get_unanswered_questionnaires(self)

    @denormalized(
        models.NullBooleanField,
        default=None,
        skip={"created", "updated", "last_sync_time"},
    )
    @depend_on_related("Answer")
    def has_unanswered_questionnaires(self):
        return self.unanswered_questionnaires().exists()

    def get_asociated_company_admin(self):
        """Get coordinator, that manages company of this user attendance"""
        if not self.team:
            return None
        return self.team.subsidiary.company.company_admin.filter(
            campaign=self.campaign,
            company_admin_approved="approved",
        )

    def get_asociated_company_admin_with_payments(self):
        return self.get_asociated_company_admin().filter(can_confirm_payments=True)

    def company_coordinator_emails(self):
        company_admins = self.get_asociated_company_admin()
        if company_admins:
            return format_html_join(
                _(" nebo "),
                '<a href="mailto:{0}">{0}</a>',
                ((ca.userprofile.user.email,) for ca in company_admins),
            )
        else:
            return format_html(
                '<a href="mailto:kontakt@dopracenakole.cz?subject={subject}">kontakt@dopracenakole.cz</a>',
                subject=_("Žádost o změnu adresy organizace, pobočky nebo týmu"),
            )

    def company_coordinator_mail_text(self):
        return format_html(
            _("Napište svému firemnímu koordinátorovi na e-mail {email_link}.")
            if self.get_asociated_company_admin()
            else _("Napište nám prosím na {email_link}."),
            email_link=self.company_coordinator_emails(),
        )

    def previous_user_attendance(self):
        previous_campaign = self.campaign.previous_campaign
        try:
            return self.userprofile.userattendance_set.get(campaign=previous_campaign)
        except UserAttendance.DoesNotExist:
            return None

    def get_random_motivation_message(self):
        message = MotivationMessage.get_random_message(self)
        return message

    def get_frequency_rank_in_team(self):
        return (
            self.team.members.order_by(
                F("frequency").desc(nulls_last=True),
                "get_rides_count_denorm",
            )
            .filter(frequency__gte=self.frequency - 0.000000001)
            .count()
        )
        # Frequency returned from the ORM is not exactly the same as in DB
        # (floating point transformations). We need to give it some extra margin to match self.

    @denormalized(
        models.FloatField,
        null=False,
        default=0,
        skip={"updated", "created", "last_sync_time"},
    )
    @depend_on_related("Trip", foreign_key="user_attendance")
    def trip_points_total(self):
        """
        Total trip points. Ignores recreational trips.
        """
        return (
            Trip.objects.filter(user_attendance=self).aggregate(
                Sum("commute_mode__points")
            )["commute_mode__points__sum"]
            or 0
        )

    @property
    def points(self):
        return self.trip_points_total or 0

    def points_display(self):
        from django.utils.translation import ugettext as _

        return str(round(self.points)) + " " + _("bodů")

    def get_admin_url(self, method="change", protocol="https"):
        try:
            site = Site.objects.get_current()
        except ImproperlyConfigured:
            site = Site(domain="configure-django-sites.com")
        return "%s://%s.%s%s" % (
            protocol,
            self.campaign.slug,
            site.domain,
            reverse(
                "admin:%s_%s_%s"
                % (self._meta.app_label, self._meta.model_name, method),
                args=[self.id],
            ),
        )

    def get_admin_delete_url(self):
        return self.get_admin_url(method="delete", protocol="http")

    def helpdesk_iframe_url(self):
        if settings.HELPDESK_IFRAME_URL:
            return (
                settings.HELPDESK_IFRAME_URL
                + "?queue={queue}&_readonly_fields_=queue,custom_dpnk-user&submitter_email={email}&custom_dpnk-user={dpnk_user}&_hide_fields_=queue,custom_dpnk-user".format(  # noqa
                    queue=settings.HELPDESK_QUEUE,
                    email=self.userprofile.user.email,
                    dpnk_user=self.get_admin_url(),
                )
            )

    def clean(self):
        if self.team and self.approved_for_team != "denied":
            team_members_count = self.team.members.exclude(pk=self.pk).count() + 1
            if self.team.campaign.too_much_members(team_members_count):
                raise ValidationError({"team": _("Tento tým již má plný počet členů")})

        if self.team and self.team.campaign != self.campaign:
            message = _(
                "Zvolená kampaň (%(campaign)s) musí být shodná s kampaní týmu (%(team)s)"
                % {
                    "campaign": self.campaign,
                    "team": self.team.campaign,
                },
            )
            raise ValidationError({"team": message, "campaign": message})

    def save(self, *args, **kwargs):
        # Automatically saving previous campaign user attendance choosed merch
        # if self.pk is None:
        #     previous_user_attendance = self.previous_user_attendance()
        #     if previous_user_attendance:
        #         if previous_user_attendance.t_shirt_size:
        #             t_shirt_size = self.campaign.tshirtsize_set.filter(
        #                 name=previous_user_attendance.t_shirt_size.name
        #             )
        #             if t_shirt_size.count() == 1:
        #                 self.t_shirt_size = t_shirt_size.first()

        #     if self.userprofile.user.is_active:
        #         register_mail(self)
        if self.team and self.team.campaign != self.campaign:
            logger.error(
                "UserAttendance campaign doesn't match team campaign",
                extra={
                    "user_attendance": self,
                    "new_team": self.team,
                    "campaign": self.campaign,
                    "team_campaign": self.team.campaign,
                },
            )
        if self.pk:
            # Delete REST API cache
            cache = util.Cache(
                key=f"{util.register_challenge_serializer_base_cache_key_name}"
                f"{self.userprofile.id}:{self.campaign.slug}"
            )
            if cache.data:
                del cache.data

        return super().save(*args, **kwargs)

    @classmethod
    def export_resource_classes(cls):
        from ..resources import UserAttendanceResource

        return {
            "user_attendance": ("User Attendance", UserAttendanceResource),
        }

    def assign_vouchers(self):
        from . import Voucher, VoucherType
        from .. import tasks

        assigned_vouchers = set()
        for voucher_type in VoucherType.objects.all():
            if (
                Voucher.objects.filter(
                    voucher_type1=voucher_type,
                    user_attendance=self,
                    campaign=self.campaign,
                ).count()
                == 0
            ):
                voucher = Voucher.objects.filter(
                    voucher_type1=voucher_type,
                    user_attendance__isnull=True,
                    campaign=self.campaign,
                ).first()
                if voucher is not None:
                    tasks.assign_voucher.delay(voucher.pk, self.pk)
                    assigned_vouchers.add(voucher_type.name)
        return assigned_vouchers

    def send_templated_notification(self, template):
        clang = get_language()
        activate(self.userprofile.language)
        try:
            icon_url = template.icon.url
        except ValueError:
            icon_url = ""
        notify.send(
            self,
            recipient=self.userprofile.user,
            verb=template.verb,
            url=template.url,
            icon=icon_url,
            indempotent=True,
            action_object=template,
        )
        activate(clang)

    def revoke_templated_notification(self, template):
        revoke_notification.send(
            self,
            recipient=self.userprofile.user,
            action_object=template,
        )

    def notifications(self):
        user_content_type = ContentType.objects.get(app_label="auth", model="user")
        user_attendance_content_type = ContentType.objects.get(
            app_label="dpnk", model="userattendance"
        )
        notifications = self.userprofile.user.notifications.filter(
            Q(
                actor_content_type=user_content_type.id,
                actor_object_id=self.userprofile.user.id,
            )
            | Q(
                actor_content_type=user_attendance_content_type.id,
                actor_object_id=self.id,
            ),
        )
        return notifications


@receiver(post_save, sender=UserAttendance)
def update_mailing_user_attendance(sender, instance, created, **kwargs):
    if not kwargs.get("raw", False):
        mailing.add_or_update_user(instance)


@receiver(post_save, sender=UserAttendance)
def assign_vouchers(sender, instance, created, **kwargs):
    if instance.payment_status == "done" or instance.payment_status == "no_admission":
        instance.assign_vouchers()
