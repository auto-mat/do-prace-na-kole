# -*- coding: utf-8 -*-
from django.template.loader import render_to_string
from smart_selects.widgets import ChainedSelect
import django.forms as forms
import smart_selects.widgets as widgets

class SelectOrCreate(forms.Select):
    underlying_form = None
    create = False

    def __init__(self, underlying_form_class, prefix="", new_description = u"Vytvořit novou položku", *args, **kwargs):
        super(forms.Select,self).__init__()
        self.new_description = new_description
        self.underlying_form_class = underlying_form_class
        self.underlying_form = self.underlying_form_class(prefix = prefix)

    def render(self, name, *args, **kwargs):
        html = super(SelectOrCreate, self).render(name, *args, **kwargs)
        widget_id = kwargs['attrs']['id']

        widget = render_to_string("form/select_or_create.html", {
            'html': html,
            'underlying_form': self.underlying_form,
            'selected': self.create,
            'id': widget_id,
            'new_description': self.new_description,
            })
        return widget

class SelectChainedOrCreate(widgets.ChainedSelect):
    underlying_form = None
    create = False

    def __init__(self, underlying_form_class, prefix="", new_description = u"Vytvořit novou položku", *args, **kwargs):
        super(widgets.ChainedSelect,self).__init__()
        for k, v in kwargs.iteritems():
            assert( k in ['chain_field', 'show_all', 'app_name', 'model_field', 'auto_choose', 'model_name'])
            setattr(self, k, v)
        self.manager = None

        self.new_description = new_description
        self.underlying_form_class = underlying_form_class
        self.underlying_form = self.underlying_form_class(prefix = prefix)

    def render(self, name, *args, **kwargs):
        html = super(SelectChainedOrCreate, self).render(name, *args, **kwargs)
        widget_id = kwargs['attrs']['id']

        widget = render_to_string("form/select_or_create.html", {
            'html': html,
            'underlying_form': self.underlying_form,
            'selected': self.create,
            'id': widget_id,
            'new_description': self.new_description,
            })
        return widget
