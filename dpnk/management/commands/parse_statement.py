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
from django.core.management.base import BaseCommand

from ...statement import parse


class Command(BaseCommand):
    help = 'Parses FIO bank statements'  # noqa

    def add_arguments(self, parser):
        parser.add_argument(
            '--days-back',
            default=7,
            type=int,
            nargs="?",
            help='Days back, for which will be the statement fetched',
        )

    def handle(self, *args, **kwargs):
        parse(days_back=kwargs['days_back'])
