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
from django import forms


class CommuteModeSelect(forms.RadioSelect):
    def render(self, name, value, **kwargs):
        # template widget rendering or crispy forms are not used for performance reasons
        # please bear in mind that this part of code has to be as quick as possible
        widget = '<fieldset class="controls btn-group" role="group">'
        counter = 0
        for choice in self.choices:
            counter += 1
            widget += '' \
                '<div class="radio btn">' \
                '   <input type="radio" {checked} name="{name}" id="id_{name}_{counter}" value="{choice}">' \
                '   <label for="id_{name}_{counter}">{choice_name}</label>' \
                '</div>'.format(
                    checked='checked="checked"' if str(choice[0]) == str(value) else '',
                    counter=counter,
                    name=name,
                    choice=choice[0],
                    choice_name=choice[1],
                )
        widget += '</fieldset>'
        return widget
