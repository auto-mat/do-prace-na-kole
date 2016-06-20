# -*- coding: utf-8 -*-

# Author: Petr Dlouhý <petr.dlouhy@auto-mat.cz>
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

from django.core.urlresolvers import reverse
from dpnk.test.tests import ViewsLogon
from dpnk.test.util import print_response  # noqa


class CompanyAdminViewTests(ViewsLogon):
    def test_edit_subsidiary(self):
        address = reverse('edit_subsidiary', kwargs={'pk': 1})
        response = self.client.get(address)
        self.assertContains(response, "Upravit adresu pobočky")
        self.assertContains(response, "11111")

    def test_edit_company(self):
        address = reverse('edit_company')
        response = self.client.get(address)
        self.assertContains(response, "Změna adresy organizace")
        self.assertContains(response, "11111")
        self.assertContains(response, "CZ1234567890")
