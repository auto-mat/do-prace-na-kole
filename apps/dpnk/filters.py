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
from django.contrib.admin import SimpleListFilter
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.utils.translation import ugettext_lazy as _

from . import models


class CampaignFilter(SimpleListFilter):
    title = _(u"Kampaň")
    parameter_name = u'campaign'
    field = 'campaign'

    def lookups(self, request, model_admin):
        if hasattr(request, 'subdomain') and request.subdomain:
            try:
                campaign = models.Campaign.objects.get(slug=request.subdomain)
            except models.Campaign.DoesNotExist:
                campaign = None
        else:
            campaign = None

        if campaign:
            current_campaign = campaign
            campaigns = [(None, current_campaign.name)]
            campaigns += [(c.slug, c.name) for c in models.Campaign.objects.exclude(slug=request.subdomain)]
            campaigns += [('all', _('All'))]
            campaigns += [('none', _('None'))]
        else:
            campaigns = [('all', _('All'))]
            campaigns += [('none', _('None'))]
            campaigns += [(c.slug, c.name) for c in models.Campaign.objects.all()]
        return campaigns

    def choices(self, changelist):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup,
                'query_string': changelist.get_query_string({
                    self.parameter_name: lookup,
                }, []),
                'display': title,
            }

    def queryset(self, request, queryset):
        if self.value() == 'all':
            return queryset
        elif self.value():
            campaign = self.value()
        else:
            campaign = request.subdomain
        campaign_queryarg = {self.field + "__slug": campaign}
        none_queryarg = {self.field: None}

        if self.value() == 'none':
            return queryset.filter(**none_queryarg).distinct()
        return queryset.filter(Q(**campaign_queryarg) | Q(**none_queryarg)).distinct()


def campaign_filter_generator(campaign_field):
    class CFilter(CampaignFilter):
        field = campaign_field
    return CFilter


class CityCampaignFilter(CampaignFilter):
    field = "subsidiaries__teams__campaign"

    def queryset(self, request, queryset):
        queryset = super(CityCampaignFilter, self).queryset(request, queryset)
        # queryset = queryset.annotate(user_count_sum=Sum('subsidiaries__teams__member_count', distinct=True))  TODO: this doesn't count because bug #10060
        return queryset


class HasVoucherFilter(SimpleListFilter):
    title = _(u"Má nějaké vouchery")
    parameter_name = u'has_voucher'
    field = 'has_voucher'

    def lookups(self, request, model_admin):
        return [
            ('yes', _('Ano')),
            ('no', _('Ne')),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(voucher__isnull=False).distinct()
        if self.value() == 'no':
            return queryset.filter(voucher__isnull=True).distinct()
        return queryset


class HasRidesFilter(SimpleListFilter):
    title = _(u"Má nějaké jízdy")
    parameter_name = u'has_rides'
    field = 'has_rides'

    def lookups(self, request, model_admin):
        return [
            ('yes', _('Ano')),
            ('no', _('Ne')),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(user_trips__isnull=False).distinct()
        if self.value() == 'no':
            return queryset.filter(user_trips__isnull=True).distinct()
        return queryset


class IsForCompanyFilter(SimpleListFilter):
    title = _(u"Je vnitrofiremní soutěž")
    parameter_name = u'is_for_company'
    field = 'is_for_company'

    def lookups(self, request, model_admin):
        return [
            ('yes', _('Ano')),
            ('no', _('Ne')),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(company__isnull=False).distinct()
        if self.value() == 'no':
            return queryset.exclude(company__isnull=False).distinct()
        return queryset


class HasTeamFilter(SimpleListFilter):
    title = _(u"Uživatel má zvolený tým")
    parameter_name = u'user_has_team'
    field = 'user_has_team'

    def lookups(self, request, model_admin):
        return [
            ('yes', _('Ano')),
            ('no', _('Ne')),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(team__isnull=False).distinct()
        if self.value() == 'no':
            return queryset.exclude(team__isnull=False).distinct()
        return queryset


class EmailFilter(SimpleListFilter):
    title = _(u"Email")
    parameter_name = u'email'

    def lookups(self, request, model_admin):
        return (
            ('duplicate', _(u'Duplicitní')),
            ('blank', _(u'Prázdný')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'duplicate':
            duplicates = User.objects.filter(email__isnull=False).\
                exclude(email__exact='').\
                values('email').\
                annotate(Count('id')).values('email').\
                order_by().filter(id__count__gt=1).\
                values_list('email', flat=True)
            return queryset.filter(email__in=duplicates)
        if self.value() == 'blank':
            return queryset.filter(email__exact='')
        return queryset


class HasUserprofileFilter(SimpleListFilter):
    title = _(u"Má userprofile")
    parameter_name = u'has_userprofile'

    def lookups(self, request, model_admin):
        return [
            ('yes', 'Yes'),
            ('no', 'No'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.exclude(userprofile=None)
        if self.value() == 'no':
            return queryset.filter(userprofile=None)
        return queryset


class HasReactionFilter(SimpleListFilter):
    title = _(u"Obsahuje odpověď")
    parameter_name = u'has_reaction'

    def lookups(self, request, model_admin):
        return (
            ('yes', u'Ano'),
            ('no', u'Ne'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.exclude((Q(comment=None) | Q(comment='')) & (Q(attachment=None) | Q(attachment='')) & Q(points_given=None)).distinct()
        if self.value() == 'no':
            return queryset.filter((Q(comment=None) | Q(comment='')) & (Q(attachment=None) | Q(attachment='')) & Q(points_given=None)).distinct()
        return queryset


class HasUserAttendanceFilter(SimpleListFilter):
    title = _(u"Má účast v kampani")
    parameter_name = u'has_user_attendance'

    def lookups(self, request, model_admin):
        return (
            ('yes', u'Ano'),
            ('no', u'Ne'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(userattendance__isnull=False)
        if self.value() == 'no':
            return queryset.filter(userattendance__isnull=True)
        return queryset


class InvoicePaidFilter(SimpleListFilter):
    title = _(u"Zaplacení faktury")
    parameter_name = u'invoice_paid'

    def lookups(self, request, model_admin):
        return (
            ('yes', u'Zaplacena'),
            ('no', u'Nezaplacena'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(paid_date__isnull=False)
        if self.value() == 'no':
            return queryset.filter(paid_date__isnull=True)
        return queryset


class TrackFilter(SimpleListFilter):
    title = _("Má nahranou trasu")
    parameter_name = 'has_track'

    def lookups(self, request, model_admin):
        return [
            ('yes', _('Ano')),
            ('no', _('Ne')),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(track__isnull=False).distinct()
        if self.value() == 'no':
            return queryset.filter(track__isnull=True).distinct()
        return queryset
