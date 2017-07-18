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

from selectable.forms.widgets import AutoCompleteSelectWidget

from smart_selects.widgets import ChainedSelect


class SelectOrCreateRenderMixin(object):
    def get_underlying_context(self, name, value, attrs):
        context = {}
        context['underlying_form'] = self.underlying_form
        context['selected'] = self.create
        context['id'] = attrs['id']
        context['new_description'] = self.new_description
        if hasattr(self, 'help_text'):
            context['help_text'] = self.help_text
        return context


class SelectOrCreateAutoComplete(SelectOrCreateRenderMixin, AutoCompleteSelectWidget):
    underlying_form = None
    create = False
    widget_template_name = "form/select_or_create.html"

    def __init__(self, channel, underlying_form_class, prefix="", new_description=u"Vytvořit novou položku", help_text=None, *args, **kwargs):
        super(SelectOrCreateAutoComplete, self).__init__(lookup_class='dpnk.lookups.CompanyLookup')
        self.new_description = new_description
        self.channel = channel
        self.underlying_form_class = underlying_form_class
        self.underlying_form = self.underlying_form_class(prefix=prefix)
        self.help_text = help_text

    def render(self, name, value, attrs=None, renderer=None):
        context = self.get_underlying_context(name, value, attrs)
        context['html'] = super().render(name, value, {**attrs, **self.attrs}, renderer)
        return self._render(self.widget_template_name, context, renderer)


class SelectChainedOrCreate(SelectOrCreateRenderMixin, ChainedSelect):
    underlying_form = None
    create = False
    sort = True
    widget_template_name = "form/select_or_create.html"

    def __init__(
            self, to_app_name, to_model_name, chained_field, chained_model_field,
            foreign_key_app_name, foreign_key_model_name, foreign_key_field_name,
            show_all, auto_choose, sort=True, manager=None, view_name=None,
            underlying_form_class=None, prefix="", new_description="Vytvořit novou položku",
    ):
        super().__init__(
            to_app_name, to_model_name, chained_field, chained_model_field,
            foreign_key_app_name, foreign_key_model_name, foreign_key_field_name,
            show_all, auto_choose, sort=True, manager=None, view_name=None,
        )
        self.manager = manager

        self.new_description = new_description
        self.underlying_form_class = underlying_form_class
        self.underlying_form = self.underlying_form_class(prefix=prefix)

    def render(self, name, value, attrs=None, choices=(), renderer=None):
        context = self.get_underlying_context(name, value, attrs)
        context['html'] = super().render(name, value, {**attrs, **self.attrs}, choices)
        return self._render(self.widget_template_name, context, renderer)


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
