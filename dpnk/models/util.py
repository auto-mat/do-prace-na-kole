# -*- coding: utf-8 -*-

# Author: Hynek Hanke <hynek.hanke@auto-mat.cz>
# Author: Petr Dlouhý <petr.dlouhy@email.cz>
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

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from ..string_lazy import format_lazy

urls = {
    'pnk_map_url':
    'https://mapa.prahounakole.cz/?zoom=13&lat=50.08741&lon=14.4211&layers=_Wgt',
    'help_url':
    reverse_lazy('help'),
}
MAP_DESCRIPTION = format_lazy(
    _("""
<br/>
<strong><a href="{help_url}" class="btn btn-primary" target="_blank">Nápověda k editace tras</a></strong>
<br/>

Trasa slouží k výpočtu vzdálenosti a pomůže nám lépe určit potřeby lidí pohybuících se ve městě na kole.
<br/>Trasy všech účastníků budou v anonymizované podobě zobrazené na <a href="{pnk_map_url}">mapě Prahou na kole</a>.
"""),
    **urls,
)
