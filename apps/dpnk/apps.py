# -*- coding: utf-8 -*-

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


from django.apps import AppConfig
from django.db.utils import ProgrammingError


class DPNKConfig(AppConfig):
    name = 'dpnk'
    verbose_name = "Do práce na kole"

    def ready(self):
        from .models import Campaign, Team, get_team_in_campaign_manager,\
            change_invoice_payments_status, Invoice, UserAttendance, pre_user_team_changed, post_user_team_changed, set_track, GpxFile
        from fieldsignals import post_save_changed, pre_save_changed
        try:
            for campaign in Campaign.objects.all():
                setattr(Team, 'team_in_campaign_%s' % campaign.slug, get_team_in_campaign_manager(campaign.slug).objects)
        except ProgrammingError:
            pass

        post_save_changed.connect(change_invoice_payments_status, sender=Invoice, fields=['paid_date'])
        pre_save_changed.connect(pre_user_team_changed, sender=UserAttendance, fields=['team'])
        post_save_changed.connect(post_user_team_changed, sender=UserAttendance, fields=['team'])
        pre_save_changed.connect(set_track, sender=GpxFile, fields=['file'])
