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

from coupons.models import DiscountCoupon

from denorm import denormalized, depend_on_related

from django.contrib.gis.db import models
from django.contrib.humanize.templatetags.humanize import intcomma
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.html import format_html, format_html_join
from django.utils.translation import ugettext_lazy as _

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
        verbose_name = _(u"Účastník kampaně")
        verbose_name_plural = _(u"Účastníci kampaně")
        unique_together = (("userprofile", "campaign"),)

    TEAMAPPROVAL = (
        ('approved', _(u"Odsouhlasený")),
        ('undecided', _(u"Nerozhodnuto")),
        ('denied', _(u"Zamítnutý")),
    )

    campaign = models.ForeignKey(
        'Campaign',
        verbose_name=_(u"Kampaň"),
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )
    userprofile = models.ForeignKey(
        "UserProfile",
        verbose_name=_(u"Uživatelský profil"),
        related_name="userattendance_set",
        unique=False,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )
    distance = models.FloatField(
        verbose_name=_(u"Vzdálenost (km)"),
        help_text=_(u"Průměrná ujetá vzdálenost z domova do práce (v km v jednom směru)"),
        default=None,
        blank=True,
        null=True,
    )
    track = models.MultiLineStringField(
        verbose_name=_(u"trasa"),
        help_text=MAP_DESCRIPTION,
        srid=4326,
        null=True,
        blank=True,
        geography=True,
    )
    dont_want_insert_track = models.BooleanField(
        verbose_name=_(u"Nepřeji si zadávat svoji trasu."),
        default=False,
        null=False,
    )
    team = models.ForeignKey(
        'Team',
        related_name='users',
        verbose_name=_(u"Tým"),
        null=True,
        blank=True,
        default=None,
        on_delete=models.SET_NULL,
    )
    approved_for_team = models.CharField(
        verbose_name=_(u"Souhlas týmu"),
        choices=TEAMAPPROVAL,
        max_length=16,
        null=False,
        default='undecided',
    )
    t_shirt_size = models.ForeignKey(
        't_shirt_delivery.TShirtSize',
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
    created = models.DateTimeField(
        verbose_name=_(u"Datum vytvoření"),
        auto_now_add=True,
        null=True,
    )
    updated = models.DateTimeField(
        verbose_name=_(u"Datum poslední změny"),
        auto_now=True,
        null=True,
    )
    personal_data_opt_in = models.BooleanField(
        verbose_name=_(u"Souhlas se zpracováním osobních údajů."),
        blank=False,
        default=False,
    )

    sandwich_model = Diploma

    def diploma(self):
        try:
            return Diploma.objects.get(obj=self)
        except Diploma.DoesNotExist:
            return None

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
    name.admin_order_field = 'userprofile__user__last_name'
    name.short_description = _(u"Jméno")

    def name_for_trusted(self):
        return self.userprofile.name_for_trusted()
    name_for_trusted.admin_order_field = 'userprofile__user__last_name'
    name_for_trusted.short_description = _(u"Jméno")

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
        price_level = self.campaign.get_current_price_level(date_time=util.today(), category=category)
        if price_level:
            base_price = price_level.price
        else:
            base_price = 0
        return (base_price + self.t_shirt_price()) * self.discount_multiplier()

    def admission_fee(self):
        return self.admission_fee_for_category('basic')

    def has_admission_fee(self):
        return self.campaign.get_current_price_level(date_time=util.today(), category='basic') is not None or \
            self.campaign.get_current_price_level(date_time=util.today(), category='company') is not None

    def beneficiary_admission_fee(self):
        return self.campaign.benefitial_admission_fee + self.t_shirt_price()

    def company_admission_fee(self):
        return self.admission_fee_for_category('company')

    def company_admission_fee_intcomma(self):
        return intcomma(self.company_admission_fee())

    @denormalized(models.ForeignKey, to='Payment', null=True, on_delete=models.SET_NULL, skip={'updated', 'created', 'last_sync_time'})
    @depend_on_related('Payment', foreign_key='payment_user_attendance', skip={'updated', 'created'})
    def representative_payment(self):
        if self.team and self.team.subsidiary and not self.has_admission_fee():
            return None

        try:
            return self.payments().filter(status__in=Payment.done_statuses).latest('id')
        except Transaction.DoesNotExist:
            pass

        try:
            return self.payments().filter(status__in=Payment.waiting_statuses).latest('id')
        except Transaction.DoesNotExist:
            pass

        try:
            return self.payments().latest('id')
        except Transaction.DoesNotExist:
            pass

        return None

    PAYMENT_CHOICES = (
        ('no_admission', _(u'neplatí se')),
        ('none', _(u'žádné platby')),
        ('done', _(u'zaplaceno')),
        ('waiting', _(u'nepotvrzeno')),
        ('unknown', _(u'neznámý')),
    )

    @denormalized(models.CharField, choices=PAYMENT_CHOICES, max_length=20, null=True, skip={'updated', 'created', 'last_sync_time'})
    @depend_on_related('Payment', foreign_key='payment_user_attendance', skip={'updated', 'created'})
    def payment_status(self):
        if self.team and self.team.subsidiary and not self.has_admission_fee():
            return 'no_admission'
        if self.admission_fee() == 0:
            return 'done'
        payment = self.representative_payment
        if not payment:
            return 'none'
        if payment.status in Payment.done_statuses:
            return 'done'
        if payment.status in Payment.waiting_statuses:
            return 'waiting'
        return 'unknown'

    def payment_class(self):
        payment_classes = {
            'no_admission': 'success',
            'none': 'error',
            'done': 'success',
            'waiting': 'warning',
            'unknown': 'warning',
        }
        return payment_classes[self.payment_status]

    def payment_type_string(self):
        if self.representative_payment:
            pay_type = self.representative_payment.pay_type
            if pay_type:
                return Payment.PAY_TYPES_DICT[pay_type]
        return _("žádná platba")

    def get_competitions(self, competition_types=None):
        from .. import results
        return results.get_competitions_with_info(self, competition_types)

    def get_rides_count(self):
        from .. import results
        try:
            return results.get_rides_count(self, self.campaign.phase("competition"))
        except Phase.DoesNotExist:
            return 0

    @denormalized(models.IntegerField, null=True, skip={'updated', 'created', 'last_sync_time'})
    @depend_on_related('Trip')
    def get_rides_count_denorm(self):
        return self.get_rides_count()

    def get_frequency(self, day=None):
        from .. import results
        try:
            return results.get_userprofile_frequency(self, self.campaign.phase("competition"), day)[2]
        except Phase.DoesNotExist:
            return 0

    @denormalized(models.FloatField, null=True, skip={'updated', 'created', 'last_sync_time'})
    @depend_on_related('Trip')
    def frequency(self):
        return self.get_frequency()

    def get_frequency_percentage(self, day=None):
        if day:
            return self.get_frequency(day) * 100
        else:
            frequency = self.frequency if self.frequency is not None else 0
            return frequency * 100

    def get_frequency_icons(self):
        frequency = self.frequency
        roles = {}
        for icon in LandingPageIcon.objects.filter(max_frequency__gte=frequency, min_frequency__lte=frequency):
            roles[icon.role] = icon.file.url

        return roles

    @denormalized(models.FloatField, null=True, skip={'updated', 'created', 'last_sync_time'})
    @depend_on_related('Trip')
    def trip_length_total(self):
        """
        Total trip length NOT including recreational trips.
        """
        from .. import results
        try:
            return results.get_userprofile_length([self], self.campaign.phase("competition"))
        except Phase.DoesNotExist:
            return 0

    def trip_length_total_rounded(self):
        return round(self.trip_length_total or 0, 2)

    @denormalized(models.FloatField, null=True, skip={'updated', 'created', 'last_sync_time'})
    @depend_on_related('Trip')
    def total_trip_length_including_recreational(self):
        from .. import results
        try:
            return results.get_userprofile_length([self], self.campaign.phase("competition"), recreational=True)
        except Phase.DoesNotExist:
            return 0

    def trip_length_total_including_recreational_rounded(self):
        return round(self.total_trip_length_including_recreational, 2)

    def get_working_rides_base_count(self):
        """ Return number of rides, that should be acomplished to this date """
        from .. import results
        return results.get_working_trips_count(self, self.campaign.phase("competition"))

    def get_remaining_rides_count(self):
        """ Return number of rides, that are remaining to the end of competition """
        competition = self.campaign.competition_phase()
        days_count = util.days_count(competition, competition.date_to)
        days_count_till_now = util.days_count(competition, util.today())
        print(days_count)
        print(days_count_till_now)
        return (days_count - days_count_till_now).days * 2

    def get_remaining_max_theoretical_frequency_percentage(self):
        """ Return maximal frequency that can be achieved till end of the competition """
        remaining_rides = self.get_remaining_rides_count()
        rides_count = self.get_rides_count_denorm
        working_rides_base = self.get_working_rides_base_count()
        print("working rides base: ", working_rides_base)
        print("rides count: ", rides_count)
        return ((rides_count + remaining_rides) / (working_rides_base + remaining_rides)) * 100

    def get_minimum_rides_base_proportional(self):
        from .. import results
        return results.get_minimum_rides_base_proportional(self.campaign.phase("competition"), util.today())

    def get_distance(self, round_digits=2):
        track = self.get_initial_track()
        if track:
            return round(util.get_multilinestring_length(track), round_digits)
        if self.distance:
            return self.distance
        else:
            return 0
    get_distance.short_description = _('Vzdálenost (km) do práce')
    get_distance.admin_order_field = 'distance'

    def get_userprofile(self):
        return self.userprofile

    def is_libero(self):
        if self.team and self.team_member_count() and self.campaign.competitors_choose_team():
            return self.team_member_count() <= 1
        else:
            return False

    def package_shipped(self):
        from t_shirt_delivery.models import PackageTransaction
        return self.transactions.filter(instance_of=PackageTransaction, status__in=PackageTransaction.shipped_statuses).last()

    def other_user_attendances(self, campaign):
        return self.userprofile.userattendance_set.exclude(campaign=campaign)

    def company(self):
        if self.team:
            return self.team.subsidiary.company

        try:
            return self.userprofile.company_admin.get(campaign=self.campaign).administrated_company
        except CompanyAdmin.DoesNotExist:
            return None

    def entered_competition_reason(self):
        if not self.userprofile.profile_complete() or not self.personal_data_opt_in:
            return 'profile_uncomplete'
        if not self.is_team_approved():
            if self.team_complete():
                return 'team_waiting'
            else:
                return 'team_uncomplete'
        if not self.tshirt_complete():
            return 'tshirt_uncomplete'
        if not self.has_paid():
            if self.payment_complete():
                return 'payment_waiting'
            else:
                return 'payment_uncomplete'
        if self.campaign.track_required and not self.track_complete():
            return 'track_uncomplete'
        return True

    def entered_competition(self):
        return self.tshirt_complete() and\
            self.is_team_approved() and\
            self.has_paid() and\
            self.userprofile.profile_complete() and\
            self.personal_data_opt_in

    def team_member_count(self):
        if self.team:
            return self.team.member_count

    def tshirt_complete(self):
        return (not self.campaign.has_any_tshirt) or self.t_shirt_size

    def track_complete(self):
        return self.track or self.distance

    def team_complete(self):
        return self.team

    def is_team_approved(self):
        return self.team and self.approved_for_team == 'approved'

    def payment_complete(self):
        return self.payment_status not in ('none', None)

    def payment_complete_date(self):
        if self.representative_payment is not None:
            if self.representative_payment.realized:
                return self.representative_payment.realized
            else:
                return self.representative_payment.created
        return self.created

    def has_paid(self):
        return self.payment_status in ('done', 'no_admission') or (not self.has_admission_fee())

    def get_emissions(self, distance=None):
        return util.get_emissions(self.trip_length_total)

    def get_active_trips(self):
        days = list(util.days_active(self.campaign.phase("competition")))
        return self.get_trips(days)

    def get_all_trips(self, day=None):
        days = list(util.days(self.campaign.phase("competition"), day))
        return self.get_trips(days)

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
        trip_days = trips.values_list('date', 'direction')
        expected_trip_days = [(day, direction) for day in days for direction in self.campaign.get_directions()]
        uncreated_trips = sorted(list(set(expected_trip_days) - set(trip_days)))
        return trips, uncreated_trips

    def get_initial_track(self):
        trips, _ = self.get_all_trips()
        previous_trip_with_track = trips.filter(track__isnull=False).order_by('-date', '-direction').first()
        if previous_trip_with_track:
            return previous_trip_with_track.track
        if self.track:
            return self.track
        return None

    @denormalized(models.ForeignKey, to='CompanyAdmin', null=True, on_delete=models.SET_NULL, skip={'updated', 'created', 'last_sync_time'})
    @depend_on_related('UserProfile', skip={'mailing_hash'})
    def related_company_admin(self):
        """ Get company coordinator profile for this user attendance """
        try:
            return CompanyAdmin.objects.get(userprofile=self.userprofile, campaign=self.campaign)
        except CompanyAdmin.DoesNotExist:
            return None

    def unanswered_questionnaires(self):
        from .. import results
        return results.get_unanswered_questionnaires(self)

    @denormalized(models.NullBooleanField, default=None, skip={'created', 'updated', 'last_sync_time'})
    @depend_on_related('Answer')
    def has_unanswered_questionnaires(self):
        return self.unanswered_questionnaires().exists()

    def get_asociated_company_admin(self):
        """ Get coordinator, that manages company of this user attendance """
        if not self.team:
            return None
        return self.team.subsidiary.company.company_admin.filter(
            campaign=self.campaign,
            company_admin_approved='approved',
        )

    def get_asociated_company_admin_with_payments(self):
        return self.get_asociated_company_admin().filter(can_confirm_payments=True)

    def company_coordinator_emails(self):
        company_admins = self.get_asociated_company_admin()
        if company_admins:
            return format_html_join(_(" nebo "), '<a href="mailto:{0}">{0}</a>', ((ca.userprofile.user.email,) for ca in company_admins))
        else:
            return format_html(
                '<a href="mailto:kontakt@dopracenakole.cz?subject={subject}">kontakt@dopracenakole.cz</a>',
                subject=_("Žádost o změnu adresy organizace, pobočky nebo týmu"),
            )

    def company_coordinator_mail_text(self):
        return format_html(
            _("Napište svému firemnímu koordinátorovi na e-mail {email_link}.") if
            self.get_asociated_company_admin() else _("Napište nám prosím na {email_link}."),
            email_link=self.company_coordinator_emails(),
        )

    def previous_user_attendance(self):
        previous_campaign = self.campaign.previous_campaign
        try:
            return self.userprofile.userattendance_set.get(campaign=previous_campaign)
        except UserAttendance.DoesNotExist:
            return None

    def clean(self):
        if self.team and self.approved_for_team != 'denied':
            team_members_count = self.team.members().exclude(pk=self.pk).count() + 1
            if self.team.campaign.too_much_members(team_members_count):
                raise ValidationError({'team': _("Tento tým již má plný počet členů")})

        if self.team and self.team.campaign != self.campaign:
            message = _(
                "Zvolená kampaň (%(campaign)s) musí být shodná s kampaní týmu (%(team)s)" % {
                    'campaign': self.campaign,
                    'team': self.team.campaign,
                },
            )
            raise ValidationError({'team': message, 'campaign': message})

    def save(self, *args, **kwargs):
        if self.pk is None:
            previous_user_attendance = self.previous_user_attendance()
            if previous_user_attendance:
                if previous_user_attendance.track:
                    self.distance = previous_user_attendance.distance
                    self.track = previous_user_attendance.track
                if previous_user_attendance.t_shirt_size:
                    t_shirt_size = self.campaign.tshirtsize_set.filter(name=previous_user_attendance.t_shirt_size.name)
                    if t_shirt_size.count() == 1:
                        self.t_shirt_size = t_shirt_size.first()

            # if self.userprofile.user.is_active:
            #     register_mail(self)
        if self.team and self.team.campaign != self.campaign:
            logger.error(
                "UserAttendance campaign doesn't match team campaign",
                extra={
                    'user_attendance': self,
                    'new_team': self.team,
                    'campaign': self.campaign,
                    'team_campaign': self.team.campaign,
                },
            )
        return super().save(*args, **kwargs)


@receiver(post_save, sender=UserAttendance)
def update_mailing_user_attendance(sender, instance, created, **kwargs):
    if not kwargs.get('raw', False):
        mailing.add_or_update_user(instance)
