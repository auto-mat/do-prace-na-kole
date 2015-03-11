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
from django.utils.translation import ugettext_lazy as _
from dpnk import models


class CampaignFilter(SimpleListFilter):
    title = _(u"Kampaň")
    parameter_name = u'campaign'
    field='campaign'

    def lookups(self, request, model_admin):
        if not request.subdomain:
            campaigns = [('all', _('All'))]
            campaigns += [(c.slug, c.name) for c in models.Campaign.objects.all()]
        else:
            current_campaign = models.Campaign.objects.get(slug=request.subdomain)
            campaigns = [(None, current_campaign.name)]
            campaigns += [(c.slug, c.name) for c in models.Campaign.objects.exclude(slug=request.subdomain)]
            campaigns += [('all', _('All'))]
        return campaigns

    def choices(self, cl):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup,
                'query_string': cl.get_query_string({
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
        return queryset.filter(campaign__slug=campaign)
