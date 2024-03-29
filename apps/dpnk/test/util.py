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
from django.core.cache import cache
from django.core.management import call_command


def print_response(response, stdout=False, filename="response.html"):
    content = response.content.decode()
    if stdout:
        print(content)
    else:
        with open(filename, "w") as f:  # pragma: no cover
            f.write(content)  # pragma: no cover


class DenormMixin(object):
    def setUp(self):
        super().setUp()
        call_command("denorm_init")

    def tearDown(self):
        super().tearDown()
        call_command("denorm_drop")


class ClearCacheMixin(object):
    def tearDown(self):
        super().tearDown()
        cache.clear()
