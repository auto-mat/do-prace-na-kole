# -*- coding: utf-8 -*-

# Author: Petr Dlouhý <petr.dlouhy@email.cz>
#
# Copyright (C) 2017 o.s. Auto*Mat
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
from django.utils.translation import ugettext_lazy as _

from dpnk.models import Campaign

from t_shirt_delivery.models import DeliveryBatch


def create_batch(modeladmin, request, queryset):
    campaign = Campaign.objects.get(slug=request.subdomain)
    delivery_batch = DeliveryBatch()
    delivery_batch.campaign = campaign
    delivery_batch.add_packages_on_save = False
    delivery_batch.save()
    delivery_batch.add_packages(user_attendances=queryset)
    delivery_batch.add_packages_on_save = True
    delivery_batch.save()
    modeladmin.message_user(request, _(u"Vytvořena nová dávka obsahující %s položek") % queryset.count())


create_batch.short_description = _(u"Vytvořit dávku z vybraných uživatelů")
