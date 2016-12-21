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
from PyPDF2 import PdfFileReader

from coupons import models

from django.test import TestCase


class DiscountCouponTests(TestCase):
    fixtures = ['campaign', 'auth_user', 'users', 'coupons']

    def test_save(self):
        discount_coupon = models.DiscountCoupon.objects.create(coupon_type_id=1)
        self.assertRegex(discount_coupon.name(), r"AA-[A-Z]{6}")
        self.assertRegex(discount_coupon.coupon_pdf.name, r"coupons\/testing-campaign\/coupon_[-]?[0-9]+\.pdf")
        pdf = PdfFileReader(discount_coupon.coupon_pdf)
        pdf_string = pdf.pages[0].extractText()
        self.assertTrue(discount_coupon.name() in pdf_string)
        self.assertTrue("Startovné Do práce na kole" in pdf_string)
        self.assertTrue("12. prosinec 2017" in pdf_string)
