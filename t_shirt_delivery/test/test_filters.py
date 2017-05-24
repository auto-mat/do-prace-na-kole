# -*- coding: utf-8 -*-

# Author: Petr Dlouhý <petr.dlouhy@auto-mat.cz>
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
from django.test import RequestFactory, TestCase

from model_mommy import mommy

from t_shirt_delivery import filters
from t_shirt_delivery.models import SubsidiaryBox


class TestAllPackagesDispatchedFilter(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("")
        self.request.subdomain = "testing-campaign"

        mommy.make('TeamPackage', dispatched=False),
        mommy.make('TeamPackage', dispatched=True),
        subsidiary_box = mommy.make('SubsidiaryBox')
        mommy.make('TeamPackage', box=subsidiary_box, dispatched=False),
        mommy.make('TeamPackage', box=subsidiary_box, dispatched=True),

    def test_yes(self):
        f = filters.AllPackagesDispatched(self.request, {"all_packages_dispatched": "yes"}, SubsidiaryBox, None)
        q = f.queryset(self.request, SubsidiaryBox.objects.all())
        self.assertEquals(q.count(), 1)

    def test_no(self):
        f = filters.AllPackagesDispatched(self.request, {"all_packages_dispatched": "no"}, SubsidiaryBox, None)
        q = f.queryset(self.request, SubsidiaryBox.objects.all())
        self.assertEquals(q.count(), 2)
