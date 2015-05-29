# -*- coding: utf-8 -*-
# Author: Petr Dlouhý <petr.dlouhy@email.cz>
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

from django.utils.translation import ugettext_lazy as _

def recalculate_competitions_results(modeladmin, request, queryset):
    for competition in queryset.all():
        competition.recalculate_results()
recalculate_competitions_results.short_description = _(u"Přepočítat výsledku vybraných soutěží")


def normalize_questionnqire_admissions(modeladmin, request, queryset):
    for competition in queryset.all():
        if competition.type != 'questionnaire' or competition.competitor_type != 'single_user':
            continue
        competition.user_attendance_competitors.clear()
        for question in competition.question_set.all():
            for answer in question.answer_set.all():
                if answer.has_any_answer():
                    competition.user_attendance_competitors.add(answer.user_attendance)
        competition.save()
normalize_questionnqire_admissions.short_description = _(u"Obnovit přihlášky podle odpovědí na dotazník")
