#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Petr Dlouhý <petr.dlouhy@auto-mat.cz>
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

"""
This script is a trick to setup a fake Django environment, since this reusable
app will be developed and tested outside any specifiv Django project.

Via ``settings.configure`` you will be able to set all necessary settings
for your app and run the tests as if you were calling ``./manage.py test``.

"""
import sys

from django.conf import settings

from django_nose import NoseTestSuiteRunner

from project.settings import test as test_settings


if not settings.configured:
    settings.configure(**test_settings.__dict__)


def runtests(*test_args, **test_kwargs):
    failures = NoseTestSuiteRunner(verbosity=2, interactive=False).run_tests(
        test_args,
        test_kwargs,
    )
    sys.exit(failures)


if __name__ == '__main__':
    runtests(*sys.argv[1:])
