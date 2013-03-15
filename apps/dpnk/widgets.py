# -*- coding: utf-8 -*-
from django.template.loader import render_to_string
import django.forms as forms

class SelectOrCreate(forms.Select):
    underlying_form = None
    create_team = False

    def __init__(self, underlying_form_class, new_description = u"Vytvořit novou položku", *args, **kwargs):
        super(forms.Select,self).__init__()
        self.new_description = new_description
        self.underlying_form_class = underlying_form_class
        self.underlying_form = self.underlying_form_class(prefix = 'team')

    def render(self, name, *args, **kwargs):
        html = super(SelectOrCreate, self).render(name, *args, **kwargs)
        widget_id = kwargs['attrs']['id']

        widget = render_to_string("form/select_or_create.html", {
            'html': html,
            'underlying_form': self.underlying_form,
            'selected': self.create_team,
            'id': widget_id,
            'new_description': self.new_description,
            })
        return widget
