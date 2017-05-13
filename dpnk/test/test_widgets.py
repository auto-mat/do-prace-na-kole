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
from django.test import TestCase

from dpnk import widgets


class CommuteModeRendererTests(TestCase):
    def test_render(self):
        """ Test render method """
        renderer = widgets.CommuteModeRenderer(
            "test_name",
            1,
            {},
            [
                (1, 'Item 1'),
                (2, 'Item 2'),
            ],
        )
        self.assertHTMLEqual(
            renderer.render(),
            '<fieldset class="controls btn-group" role="group">'
            '    <div class="radio btn">'
            '        <input type="radio" checked="checked" name="test_name" id="id_test_name_1" value="1">'
            '        <label for="id_test_name_1">Item 1</label>'
            '    </div>'
            '    <div class="radio btn">'
            '        <input type="radio"  name="test_name" id="id_test_name_2" value="2"> '
            '        <label for="id_test_name_2">Item 2</label>'
            '    </div>'
            '</fieldset>',
        )

    def test_render_str(self):
        """ Test render method if the value is string and item int """
        renderer = widgets.CommuteModeRenderer(
            "test name",
            '1',
            {},
            [(1, 'Item 1')],
        )
        self.assertHTMLEqual(
            renderer.render(),
            '<fieldset class="controls btn-group" role="group">'
            '    <div class="radio btn">'
            '        <input type="radio" checked="checked" name="test name" id="id_test name_1" value="1">'
            '        <label for="id_test name_1">Item 1</label>'
            '    </div>'
            '</fieldset>',
        )
