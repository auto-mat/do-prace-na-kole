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
import datetime

from django import forms
from django.contrib.gis.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.html import escape
from django.utils.translation import string_concat, ungettext_lazy
from django.utils.translation import ugettext_lazy as _

from rank import Rank, UpperRank

from redactor.widgets import RedactorEditor

from .campaign import Campaign
from .city import City
from .company import Company
from .team import Team, TeamName
from .user_attendance import UserAttendance
from .user_profile import UserProfile
from .. import util


class Competition(models.Model):
    """Soutěžní kategorie"""

    CTYPES = (
        ('length', _(u"Ujetá vzdálenost")),
        ('frequency', _(u"Pravidelnost jízd na kole")),
        ('questionnaire', _(u"Dotazník")),
    )

    CCOMPETITORTYPES = (
        ('single_user', _(u"Jednotliví soutěžící")),
        ('liberos', _(u"Liberos")),
        ('team', _(u"Týmy")),
        ('company', _(u"Soutěž organizací")),
    )

    class Meta:
        verbose_name = _(u"Soutěžní kategorie")
        verbose_name_plural = _(u"Soutěžní kategorie")
        ordering = ('-campaign', 'name')

    name = models.CharField(
        unique=False,
        verbose_name=_(u"Jméno soutěže"),
        max_length=160, null=False,
    )
    campaign = models.ForeignKey(
        Campaign,
        verbose_name=_(u"Kampaň"),
        null=False,
        blank=False,
    )
    slug = models.SlugField(
        unique=True,
        default="",
        verbose_name=u"Doména v URL",
        blank=False,
    )
    url = models.URLField(
        default="",
        verbose_name=_("Odkaz na stránku soutěže"),
        help_text=_(u"Odkaz na stránku, kde budou pravidla a podrobné informace o soutěži"),
        null=True,
        blank=True,
    )
    date_from = models.DateField(
        verbose_name=_(u"Datum začátku soutěže"),
        help_text=_(u"Od tohoto data se počítají jízdy"),
        default=None,
        null=True,
        blank=True,
    )
    date_to = models.DateField(
        verbose_name=_(u"Datum konce soutěže"),
        help_text=_(u"Po tomto datu nebude možné soutěžit (vyplňovat dotazník)"),
        default=None,
        null=True,
        blank=True,
    )
    competition_type = models.CharField(
        verbose_name=_(u"Typ"),
        help_text=_(
            u"Určuje, zdali bude soutěž výkonnostní (na ujetou vzdálenost),"
            u" nebo na pravidelnost. Volba \"Dotazník\" slouží pro kreativní soutěže,"
            u" cyklozaměstnavatele roku a další dotazníky; je nutné definovat otázky."),
        choices=CTYPES,
        max_length=16,
        null=False,
    )
    competitor_type = models.CharField(
        verbose_name=_(u"Typ soutěžícího"),
        help_text=_(u"Určuje, zdali bude soutěž týmová, nebo pro jednotlivce. Ostatní volby vybírejte jen pokud víte, k čemu slouží."),
        choices=CCOMPETITORTYPES,
        max_length=16,
        null=False,
    )
    user_attendance_competitors = models.ManyToManyField(
        UserAttendance,
        verbose_name=_(u"Přihlášení soutěžící jednotlivci"),
        related_name="competitions",
        blank=True,
    )
    team_competitors = models.ManyToManyField(
        Team,
        verbose_name=_(u"Přihlášené soutěžící týmy"),
        related_name="competitions",
        blank=True,
    )
    company_competitors = models.ManyToManyField(
        Company,
        verbose_name=_(u"Přihlášené soutěžící organizace"),
        related_name="competitions",
        blank=True,
    )
    city = models.ManyToManyField(
        City,
        verbose_name=_(u"Soutěž pouze pro města"),
        help_text=_(u"Soutěž bude probíhat ve vybraných městech. Pokud zůstane prázdné, soutěž probíhá ve všech městech."),
        blank=True,
    )
    company = models.ForeignKey(
        Company,
        verbose_name=_(u"Soutěž pouze pro organizace"),
        null=True,
        blank=True,
    )
    sex = models.CharField(
        verbose_name=_(u"Soutěž pouze pro pohlaví"),
        help_text=_(u"Pokud chcete oddělit výsledky pro muže a ženy, je potřeba vypsat dvě soutěže - jednu pro muže a druhou pro ženy. Jinak nechte prázdné."),
        choices=UserProfile.GENDER,
        default=None,
        max_length=50,
        null=True,
        blank=True,
    )
    minimum_rides_base = models.PositiveIntegerField(
        verbose_name=_("Minimální základ počtu jízd"),
        help_text=_("Minimální počet jízd, které je nutné si zapsat, aby bylo možné dosáhnout 100% jízd"),
        default=28,
        blank=False,
        null=False,
    )
    without_admission = models.BooleanField(
        verbose_name=_(u"Soutěž bez přihlášek (pro všechny)"),
        help_text=_(u"Dotazník je obvykle na přihlášky, výkonnost také a pravidelnost bez nich."),
        default=True,
        null=False,
    )
    public_answers = models.BooleanField(
        verbose_name=_(u"Zveřejňovat soutěžní odpovědi"),
        default=False,
        null=False,
    )
    is_public = models.BooleanField(
        verbose_name=_(u"Soutěž je veřejná"),
        default=True,
        null=False,
    )
    show_results = models.BooleanField(
        verbose_name=_("Zobrazovat výsledky soutěže"),
        default=True,
        null=False,
    )
    entry_after_beginning_days = models.IntegerField(
        verbose_name=_(u"Prodloužené přihlášky"),
        help_text=_(u"Počet dní po začátku soutěže, kdy je ještě možné se přihlásit"),
        default=7,
        blank=False,
        null=False,
    )
    rules = models.TextField(
        verbose_name=_(u"Pravidla soutěže"),
        default=None,
        blank=True,
        null=True,
    )

    def get_minimum_rides_base(self):
        return self.minimum_rides_base

    def show_competition_results(self):
        if self.competition_type == 'questionnaire' and not self.has_finished():
            return False
        return self.show_results

    def get_competitors(self, potencial_competitors=False):
        from .. import results
        return results.get_competitors(self, potencial_competitors)

    def get_competitors_count(self):
        return self.get_competitors().count()

    def get_results(self):
        from .. import results
        return results.get_results(self)

    def select_related_results(self, results):
        """
        Add select_related objects to the results queryeset
        which are needed to display results.
        """
        if self.competitor_type == 'single_user' or self.competitor_type == 'libero':
            results = results.select_related(
                'user_attendance__userprofile__user',
                'user_attendance__team__subsidiary__company',
                'user_attendance__team__subsidiary__city',
            )
        elif self.competitor_type == 'team':
            results = results.select_related(
                'team__subsidiary__company',
                'team__subsidiary__city',
            )
        elif self.competitor_type == 'company':
            results = results.select_related(
                'company',
            )
        return results

    def annotate_results_rank(self, results):
        """
        Annotate results list with lower_rank and upper_rank.
        The result cannot be filtered, so use get_result_id_rank_list function to get the rank list.
        """
        results = results.annotate(
            lower_rank=Rank('result'),
            upper_rank=UpperRank('result'),
        )
        return results

    def get_result_id_rank_dict(self, results):
        """
        Make dict {result_id: (lower_rank, upper_rank)} out from results annotated with their ranks.
        """
        return {i[0]: i[1:] for i in results.values_list('id', 'lower_rank', 'upper_rank')}

    def get_results_first3(self):
        ret_list = []
        order = 1
        last_result = None
        from .. import results
        for result in results.get_results(self).all()[:100]:
            if last_result != result.result:
                order += 1
            last_result = result.result
            ret_list.append(result)
            if order > 3:
                return ret_list
        return ret_list

    def has_started(self):
        if self.date_from:
            return self.date_from <= util.today()
        else:
            return True

    def has_entry_not_opened(self):
        if self.date_from:
            return self.date_from + datetime.timedelta(self.entry_after_beginning_days) <= util.today()
        else:
            return False

    def has_finished(self):
        if self.date_to:
            return not self.date_to >= util.today()
        else:
            return False

    def is_actual(self):
        return self.has_started() and not self.has_finished()

    def recalculate_results(self):
        from .. import results
        return results.recalculate_result_competition(self)

    def get_company_querystring(self):
        """
        Returns string with wich is possible to filter results of this competition by company.
        """
        if self.competitor_type == 'single_user':
            return 'user_attendance__team__subsidiary__company'
        elif self.competitor_type == 'team':
            return 'team__subsidiary__company'
        elif self.competitor_type == 'company':
            return 'company'

    def can_admit(self, user_attendance):
        """
        Returns True if user can admit for this competition, othervise it returns the reason why user can't admit.
        """
        if self.without_admission:
            return 'without_admission'
        if not util.get_company_admin(user_attendance.userprofile.user, self.campaign) and self.competitor_type == 'company':
            return 'not_company_admin'
        if self.competition_type == 'questionnaire' and not self.has_started():
            return 'before_beginning'
        if self.competition_type == 'questionnaire' and self.has_finished():
            return 'after_end'
        if self.competition_type != 'questionnaire' and self.has_entry_not_opened():
            return 'after_beginning'

        if self.competitor_type == 'liberos' and not user_attendance.is_libero():
            return 'not_libero'
        if self.company and self.company != user_attendance.team.subsidiary.company:
            return 'not_for_company'
        if self.city.exists() and not self.city.filter(pk=user_attendance.team.subsidiary.city.pk).exists():
            return 'not_for_city'

        return True

    def get_columns(self):
        columns = [('result_order', 'get_sequence_range', _("Po&shy;řa&shy;dí"))]

        if self.competitor_type not in ('single_user', 'liberos') and self.competition_type != 'questionnaire':
            average_string = _(" prů&shy;měr&shy;ně")
        else:
            average_string = ""

        columns.append(
            {
                'length': ('result_value', 'get_result', _("Ki&shy;lo&shy;me&shy;trů%s" % average_string)),
                'frequency': ('result_value', 'get_result_percentage', _("%% jízd%s" % average_string)),
                'questionnaire': ('result_value', 'get_result', _("Bo&shy;dů%s" % average_string)),
            }[self.competition_type],
        )

        if self.competition_type == 'frequency':
            columns.append(('result_divident', 'result_divident', _("Po&shy;čet za&shy;po&shy;čí&shy;ta&shy;ných jí&shy;zd")))
            columns.append(('result_divisor', 'result_divisor', _("Cel&shy;ko&shy;vý po&shy;čet cest")))
        elif self.competition_type == 'length' and self.competitor_type == 'team':
            columns.append(('result_divident', 'result_divident', _("Po&shy;čet za&shy;po&shy;čí&shy;ta&shy;ných ki&shy;lo&shy;me&shy;trů")))

        if self.competitor_type not in ('single_user', 'liberos', 'company'):
            where = {
                'team': _("v&nbsp;tý&shy;mu"),
                'single_user': "",
                'liberos': "",
                'company': _("ve&nbsp;fir&shy;mě"),
            }[self.competitor_type]
            columns.append(('member_count', 'team__member_count', _("Po&shy;čet sou&shy;tě&shy;ží&shy;cí&shy;ch %s" % where)))

        competitor = {
            'team': 'get_team',
            'single_user': 'user_attendance',
            'liberos': 'user_attendance',
            'company': 'get_company',
        }[self.competitor_type]
        columns.append(('competitor', competitor, _("Sou&shy;tě&shy;ží&shy;cí")))

        if self.competitor_type not in ('team', 'company'):
            columns.append(('team', 'get_team', _("Tým")))

        if self.competitor_type != 'company':
            columns.append(('company', 'get_company', _("Spo&shy;leč&shy;nost")))

        columns.append(('city', 'get_city', _("Měs&shy;to")))
        return columns

    def has_admission(self, userprofile):
        if not userprofile.entered_competition():
            return False
        if self.competitor_type == 'liberos' and not userprofile.is_libero():
            return False
        if self.company and userprofile.team and self.company != userprofile.team.subsidiary.company:
            return False
        if userprofile.team and self.city.exists() and not self.city.filter(pk=userprofile.team.subsidiary.city.pk).exists():
            return False

        if self.without_admission:
            return True
        else:
            if self.competitor_type == 'single_user' or self.competitor_type == 'liberos':
                return self.user_attendance_competitors.filter(pk=userprofile.pk).exists()
            elif self.competitor_type == 'team' and userprofile.team:
                return self.team_competitors.filter(pk=userprofile.team.pk).exists()
            elif self.competitor_type == 'company' and userprofile.company():
                return self.company_competitors.filter(pk=userprofile.company().pk).exists()
            return True

    def make_admission(self, userprofile, admission=True):
        if not self.without_admission and self.can_admit(userprofile):
            if self.competitor_type == 'single_user' or self.competitor_type == 'liberos':
                if admission:
                    self.user_attendance_competitors.add(userprofile)
                else:
                    self.user_attendance_competitors.remove(userprofile)
            elif self.competitor_type == 'team':
                if admission:
                    self.team_competitors.add(userprofile.team)
                else:
                    self.team_competitors.remove(userprofile.team)
            elif self.competitor_type == 'company':
                if admission:
                    self.company_competitors.add(userprofile.company())
                else:
                    self.company_competitors.remove(userprofile.company())
        from .. import results
        results.recalculate_result_competitor_nothread(userprofile)

    def type_string(self):
        CTYPES_STRINGS = {
            'questionnaire': _('dotazník'),
            'frequency': _('soutěž na pravidelnost'),
            'length': _('soutěž na vzdálenost'),
        }
        CCOMPETITORTYPES_STRINGS = {
            'single_user': _('jednotlivců'),
            'liberos': _('liberos'),
            'team': _('týmů'),
            'company': _('společností'),
        }
        SEX_STRINGS = {
            'male': _('pro muže'),
            'female': _('pro ženy'),
        }
        if self.company:
            company_string_before = _("vnitrofiremní")
            company_string_after = _("organizace %s") % escape(self.company)
        else:
            company_string_before = ""
            company_string_after = ""

        cities = self.city.all()
        if cities:
            city_string = ungettext_lazy(
                "ve městě %(cities)s",
                "ve městech %(cities)s",
                len(cities),
            ) % {
                'cities': ", ".join([city.name for city in cities]),
            }
        else:
            city_string = ""

        if self.sex:
            sex_string = SEX_STRINGS[self.sex]
        else:
            sex_string = ""

        return string_concat(
            company_string_before, " ",
            CTYPES_STRINGS[self.competition_type], " ",
            CCOMPETITORTYPES_STRINGS[self.competitor_type], " ",
            company_string_after, " ",
            city_string, " ",
            sex_string,
        )

    def __str__(self):
        return "%s" % self.name


class CompetitionForm(forms.ModelForm):
    class Meta:
        model = Competition
        exclude = ()
        widgets = {
            'rules': RedactorEditor(),
        }

    def set_fields_queryset_on_update(self):
        if hasattr(self.instance, 'campaign') and 'user_attendance_competitors' in self.fields:
            if self.instance.competitor_type in ['liberos', 'single_user']:
                queryset = self.instance.get_competitors(potencial_competitors=True)
            else:
                queryset = self.instance.user_attendance_competitors
            queryset = queryset.select_related('userprofile__user', 'campaign')
            self.fields['user_attendance_competitors'].queryset = queryset

        if 'team_competitors' in self.fields:
            if self.instance.competitor_type == 'team':
                self.fields['team_competitors'].queryset = TeamName.objects.all()
            else:
                self.fields['team_competitors'].queryset = self.instance.team_competitors.all()

        if 'company_competitors' in self.fields:
            if self.instance.competitor_type == 'company':
                self.fields["company_competitors"].queryset = Company.objects.all()
            else:
                self.fields['company_competitors'].queryset = self.instance.company_competitors.all()

    def set_fields_queryset_on_create(self):
        if 'team_competitors' in self.fields:
            self.fields["team_competitors"].queryset = Team.objects.none()
        if 'user_attendance_competitors' in self.fields:
            self.fields["user_attendance_competitors"].queryset = UserAttendance.objects.none()
        if 'company_competitors' in self.fields:
            self.fields["company_competitors"].queryset = Company.objects.none()

    def __init__(self, *args, **kwargs):
        super(CompetitionForm, self).__init__(*args, **kwargs)
        if not hasattr(self.instance, 'campaign'):
            self.instance.campaign = Campaign.objects.get(slug=self.request.subdomain)

        if hasattr(self, "request") and not self.request.user.is_superuser:
            self.fields["city"].queryset = self.request.user.userprofile.administrated_cities
            self.fields["city"].required = True

        if self.instance.id:
            self.set_fields_queryset_on_update()
        else:
            self.set_fields_queryset_on_create()


@receiver(post_save, sender=Competition)
def competition_post_save(sender, instance, **kwargs):
    from .. import tasks
    tasks.recalculate_competitions_results.apply_async(args=((instance,),))
