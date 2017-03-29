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
from django.template.loader import render_to_string

from selectable.forms.widgets import AutoCompleteSelectWidget

from smart_selects import widgets


class SelectOrCreateAutoComplete(AutoCompleteSelectWidget):
    underlying_form = None
    create = False

    def __init__(self, channel, underlying_form_class, prefix="", new_description=u"Vytvořit novou položku", *args, **kwargs):
        super(SelectOrCreateAutoComplete, self).__init__(lookup_class='dpnk.lookups.CompanyLookup')
        self.new_description = new_description
        self.channel = channel
        self.underlying_form_class = underlying_form_class
        self.underlying_form = self.underlying_form_class(prefix=prefix)

    def render(self, name, *args, **kwargs):
        html = super(SelectOrCreateAutoComplete, self).render(name, *args, **kwargs)
        widget_id = kwargs['attrs']['id']

        widget = render_to_string(
            "form/select_or_create.html",
            {
                'html': html,
                'underlying_form': self.underlying_form,
                'selected': self.create,
                'id': widget_id,
                'new_description': self.new_description,
            },
        )
        return widget


class SelectOrCreate(forms.Select):
    underlying_form = None
    create = False

    def __init__(self, underlying_form_class, prefix="", new_description=u"Vytvořit novou položku", *args, **kwargs):
        super(forms.Select, self).__init__()
        self.new_description = new_description
        self.underlying_form_class = underlying_form_class
        self.underlying_form = self.underlying_form_class(prefix=prefix)

    def render(self, name, *args, **kwargs):
        html = super(SelectOrCreate, self).render(name, *args, **kwargs)
        widget_id = kwargs['attrs']['id']

        widget = render_to_string(
            "form/select_or_create.html",
            {
                'html': html,
                'underlying_form': self.underlying_form,
                'selected': self.create,
                'id': widget_id,
                'new_description': self.new_description,
            },
        )
        return widget


class SelectChainedOrCreate(widgets.ChainedSelect):
    underlying_form = None
    create = False
    sort = True

    def __init__(self, underlying_form_class, prefix="", new_description=u"Vytvořit novou položku", *args, **kwargs):
        super(widgets.ChainedSelect, self).__init__()
        for k, v in kwargs.items():
            assert(k in [
                'chained_field',
                'chained_model_field',
                'show_all',
                'to_app_name',
                'foreign_key_app_name',
                'foreign_key_model_name',
                'foreign_key_field_name',
                'to_model_field',
                'auto_choose',
                'to_model_name',
                'manager',
                'view_name',
            ])
            setattr(self, k, v)
        self.manager = None

        self.new_description = new_description
        self.underlying_form_class = underlying_form_class
        self.underlying_form = self.underlying_form_class(prefix=prefix)

    def render(self, name, *args, **kwargs):
        html = super(SelectChainedOrCreate, self).render(name, *args, **kwargs)
        widget_id = kwargs['attrs']['id']

        widget = render_to_string(
            "form/select_or_create.html", {
                'html': html,
                'underlying_form': self.underlying_form,
                'selected': self.create,
                'id': widget_id,
                'new_description': self.new_description,
            },
        )
        return widget


class CommuteModeRenderer(object):
    def __init__(self, name, value, attrs, choices):
        self.name = name
        self.value = value
        self.attrs = attrs
        self.choices = choices

    def render(self):
        # template widget rendering or crispy forms are not used for performance reasons
        # please bear in mind that this part of code has to be quick as possible
        widget = '<fieldset class="controls btn-group" role="group">'
        counter = 0
        for choice in self.choices:
            counter += 1
            widget += '' \
                '<div class="radio btn">' \
                '   <input type="radio" {checked} name="{name}" id="id_{name}_{counter}" value="{choice}">' \
                '   <label for="id_{name}_{counter}">{choice_name}</label>' \
                '</div>'.format(
                    checked='checked="checked"' if choice[0] == self.value else '',
                    counter=counter,
                    name=self.name,
                    choice=choice[0],
                    choice_name=choice[1],
                )
        widget += '</fieldset>'
        return widget


class CommuteModeSelect(forms.RadioSelect):
    renderer = CommuteModeRenderer
