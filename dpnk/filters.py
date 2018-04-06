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
from django.contrib.gis.db.models.functions import Length
from django.db.models import Count, Q
from django.utils.translation import ugettext_lazy as _

from psc.models import PSC

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
                'query_string': changelist.get_query_string(
                    {
                        self.parameter_name: lookup,
                    },
                    [],
                ),
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
        queryset = super().queryset(request, queryset)
        # TODO: this doesn't count because bug #10060
        # queryset = queryset.annotate(user_count_sum=Sum('subsidiaries__teams__member_count', distinct=True))
        return queryset


class DuplicateFilter(SimpleListFilter):
    def lookups(self, request, model_admin):
        return (
            ('duplicate', _(u'Duplicitní')),
            ('blank', _(u'Prázdný')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'duplicate':
            duplicates = self.filter_model.objects.filter(
                **{'%s__isnull' % self.filter_field: False},
            ).exclude(
                **{'%s__exact' % self.filter_field: self.blank_value},
            ).values(
                self.filter_field,
            ).annotate(
                Count('id'),
            ).values(
                self.filter_field,
            ). order_by().filter(
                id__count__gt=1,
            ).values_list(
                self.filter_field,
                flat=True,
            )
            return queryset.filter(
                **{'%s__in' % self.filter_field: duplicates},
            )
        if self.value() == 'blank':
            return queryset.filter(
                **{'%s__exact' % self.filter_field: self.blank_value},
            )
        return queryset


class EmailFilter(DuplicateFilter):
    title = _("E-mail")
    parameter_name = 'email_state'
    filter_field = 'email'
    filter_model = User
    blank_value = ''


class BadTrackFilter(SimpleListFilter):
    title = _("Trasa")
    parameter_name = 'track'

    def lookups(self, request, model_admin):
        return [
            ('blank', _('Prázdná')),
            ('valid', _('Platná')),
            ('invalid', _('Neplatná')),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'blank':
            queryset = queryset.filter(track__isnull=True)
            return queryset

        if self.value() in ('valid', 'invalid'):
            queryset = queryset.annotate(length=Length('track'))
            if self.value() == 'valid':
                queryset = queryset.filter(length__gt=0)
            else:
                queryset = queryset.filter(length__lte=0)
            return queryset
        return queryset


class ICOFilter(DuplicateFilter):
    title = _("IČO")
    parameter_name = 'ico_state'
    filter_field = 'ico'
    filter_model = models.Company
    blank_value = None


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


class PSCFilter(SimpleListFilter):
    title = _("PSČ")
    parameter_name = 'psc'

    def lookups(self, request, model_admin):
        return [
            ('valid', _('Platná')),
            ('invalid', _('Neplatná')),
        ]

    def queryset(self, request, queryset):
        if self.value() in ('valid', 'invalid'):
            psc_list = PSC.objects.values('psc').distinct()
            if self.value() == 'valid':
                return queryset.filter(address_psc__in=psc_list)
            else:
                return queryset.exclude(address_psc__in=psc_list)
        return queryset


class ActiveCityFilter(SimpleListFilter):
    title = _("Město aktivní")
    parameter_name = 'city_active'

    def lookups(self, request, model_admin):
        return [
            ('yes', _('Ano')),
            ('no', _('Ne')),
        ]

    def queryset(self, request, queryset):
        if hasattr(request, 'campaign'):
            campaign = request.campaign
            active_city_kwargs = {"city__cityincampaign__in": campaign.cityincampaign_set.all()}
            if self.value() == 'yes':
                return queryset.filter(**active_city_kwargs)
            if self.value() == 'no':
                return queryset.exclude(**active_city_kwargs)
