# -*- coding: utf-8 -*-

# Author: Petr Dlouhý <petr.dlouhy@auto-mat.cz>
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


from dpnk.models import UserAttendance

from model_mommy.recipe import Recipe, foreign_key, related

PhaseRecipe = Recipe(
    "dpnk.Phase",
    phase_type="competition",
    date_from="2010-1-1",
    date_to="2020-1-1",
    campaign__slug="temporary-campaign",  # this will be overriden by the related campaign
    campaign__name="Temporary campaign",
)
CampaignRecipe = Recipe(
    "Campaign",
    slug="testing-campaign",
    phase_set=related(PhaseRecipe),
)
UserAttendanceRecipe = Recipe(
    UserAttendance,
    campaign=foreign_key(CampaignRecipe),
)
