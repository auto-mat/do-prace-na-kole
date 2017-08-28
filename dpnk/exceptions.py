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

from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden
from django.template import loader
from django.utils.translation import ugettext_lazy as _
from django.views import defaults


class TemplatePermissionDenied(PermissionDenied):
    def __init__(self, message, template_name='403.html'):
        self.template_name = template_name
        self.message = message
        return super().__init__(self, message)

    def __str__(self):
        return str(self.message)


def permission_denied_view(request, exception, template_name=defaults.ERROR_403_TEMPLATE_NAME):
    if hasattr(exception, 'template_name'):
        template_name = exception.template_name
        template = loader.get_template(template_name)
        return HttpResponseForbidden(
            template.render(
                request=request,
                context={
                    'fullpage_error_message': str(exception),
                    'title': _('Přístup odepřen'),
                },
            ),
        )

    return defaults.permission_denied(request, exception, template_name)
