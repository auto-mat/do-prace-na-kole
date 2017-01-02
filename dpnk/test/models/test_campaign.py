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
from django.test import TestCase

from dpnk import models


class TestCampaignMethods(TestCase):
    def test_phase(self):
        """
        Test that phase caching works properly
        """
        campaign = models.Campaign.objects.create(name="Campaign", slug="campaign")
        phase = models.Phase.objects.create(campaign=campaign, phase_type="competition")
        self.assertEqual(campaign.phase("competition"), phase)

        campaign1 = models.Campaign.objects.create(name="Campaign 1", slug="campaign1")
        phase1 = models.Phase.objects.create(campaign=campaign1, phase_type="competition")
        self.assertEqual(campaign1.phase("competition"), phase1)

    def test_late_admission_phase_actual(self):
        """
        Test that late_admission_phase_actual function works properly
        """
        campaign = models.Campaign.objects.create(name="Campaign", slug="campaign")
        models.Phase.objects.create(campaign=campaign, phase_type="late_admission")
        self.assertEqual(campaign.late_admission_phase_actual(), True)

    def test_late_admission_phase_actual_no_phase(self):
        """
        Test that late_admission_phase_actual function works properly if no phase is found
        """
        campaign = models.Campaign.objects.create(name="Campaign", slug="campaign")
        self.assertEqual(campaign.late_admission_phase_actual(), True)
