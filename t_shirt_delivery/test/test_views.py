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
from unittest.mock import patch

import denorm

from django.core.urlresolvers import reverse

from dpnk.models import Payment
from dpnk.test.test_views import ViewsLogon

from price_level.models import PriceLevel

from t_shirt_delivery.models import PackageTransaction, TShirtSize


class ViewsTestsLogon(ViewsLogon):
    def test_dpnk_t_shirt_size(self):
        post_data = {
            't_shirt_size': '1',
            'next': 'Next',
        }
        PackageTransaction.objects.all().delete()
        Payment.objects.all().delete()
        self.user_attendance.save()
        response = self.client.post(reverse('zmenit_triko'), post_data, follow=True)
        self.assertRedirects(response, reverse("typ_platby"))
        self.assertTrue(self.user_attendance.t_shirt_size.pk, 1)

    def test_dpnk_t_shirt_size_no_sizes(self):
        PackageTransaction.objects.all().delete()
        Payment.objects.all().delete()
        TShirtSize.objects.all().delete()
        self.user_attendance.t_shirt_size = None
        self.user_attendance.save()
        self.user_attendance.campaign.save()
        denorm.flush()
        response = self.client.get(reverse('zmenit_triko'))
        self.assertRedirects(response, reverse("typ_platby"), target_status_code=403)

    @patch('slumber.API')
    def test_dpnk_t_shirt_size_no_sizes_no_admission(self, slumber_api):
        slumber_api.feed.get = {}
        PackageTransaction.objects.all().delete()
        Payment.objects.all().delete()
        TShirtSize.objects.all().delete()
        self.user_attendance.t_shirt_size = None
        self.user_attendance.save()
        PriceLevel.objects.all().delete()
        self.user_attendance.campaign.save()
        denorm.flush()
        response = self.client.get(reverse('zmenit_triko'), follow=True)
        self.assertRedirects(response, reverse("profil"))

    def test_dpnk_t_shirt_size_no_team(self):
        PackageTransaction.objects.all().delete()
        Payment.objects.all().delete()
        self.user_attendance.save()
        self.user_attendance.team = None
        self.user_attendance.save()
        response = self.client.get(reverse('zmenit_triko'))
        self.assertContains(response, "Velikost trička nemůžete měnit, dokud nemáte zvolený tým.", status_code=403)
