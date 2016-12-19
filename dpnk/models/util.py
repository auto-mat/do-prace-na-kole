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

from django.utils.translation import ugettext_lazy as _

MAP_DESCRIPTION = _("""
<ul>
   <li><strong>Zadávání trasy zahájíte kliknutím na tlačítko "Nakreslit trasu", ukončíte kliknutím na cílový bod.</strong></li>
   <li>Změnu trasy provedete po přepnutí do režimu úprav kliknutím na trasu.</li>
   <li>Trasu stačí zadat tak, že bude zřejmé, kterými ulicemi vede.</li>
   <li>Zadání přesnějšího průběhu nám však může pomoci lépe zjistit jak se lidé na kole pohybují.</li>
   <li>Trasu bude možné změnit nebo upřesnit i později v průběhu soutěže.</li>
   <li>Polohu začátku a konce trasy stačí zadávat s přesností 100m.</li>
</ul>
Trasa slouží k výpočtu vzdálenosti a pomůže nám lépe určit potřeby lidí pohybuících se ve městě na kole. Vaše cesta se zobrazí vašim týmovým kolegům.
<br/>Trasy všech účastníků budou v anonymizované podobě zobrazené na úvodní stránce.
""")
