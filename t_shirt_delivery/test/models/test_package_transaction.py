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

from model_mommy import mommy


class TestMethods(TestCase):
    def test_package_transaction_raises_sequence_number_overrun(self):
        phase = mommy.make(
            "dpnk.Phase",
            campaign__tracking_number_first=1,
            campaign__tracking_number_last=1,
            phase_type="competition",
            date_from="2016-1-1",
            date_to="2016-1-1",
        )
        package_transaction = mommy.make(
            "PackageTransaction",
            delivery_batch__campaign=phase.campaign,
            user_attendance__campaign=phase.campaign,
            tracking_number=None,
        )
        self.assertEqual(package_transaction.tracking_number, 1)
        with self.assertRaisesRegexp(Exception, "Došla číselná řada pro balíčkové transakce"):
            package_transaction = mommy.make(
                "PackageTransaction",
                delivery_batch__campaign=phase.campaign,
                user_attendance__campaign=phase.campaign,
                tracking_number=None,
            )
