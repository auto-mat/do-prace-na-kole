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

from django.contrib.gis.db import models
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from model_utils.models import TimeStampedModel

from . import PackageTransaction
from .. import customer_sheets


class SubsidiaryBox(TimeStampedModel, models.Model):
    """ Krabice pro pobočku """

    class Meta:
        verbose_name = _("Krabice pro pobočku")
        verbose_name_plural = _("Krabice pro pobočky")

    delivery_batch = models.ForeignKey(
        'DeliveryBatch',
        verbose_name=_("Dávka objednávek"),
        null=False,
        blank=False,
    )
    customer_sheets = models.FileField(
        verbose_name=_(u"Zákaznické listy"),
        upload_to=u'customer_sheets',
        blank=True,
        null=True,
    )
    subsidiary = models.ForeignKey(
        'dpnk.Subsidiary',
        verbose_name=_("Pobočka"),
        null=True,
        blank=True,
    )

    def __str__(self):
        return _("Krabice pro pobočku %s") % self.subsidiary

    def get_representative_user_attendance(self):
        """ Returns UserAttendance to which this box should be addressed """
        team_package = self.teampackage_set.first()
        if not team_package:
            return None
        package = team_package.packagetransaction_set.first()
        if not package:
            return None
        return self.teampackage_set.first().packagetransaction_set.first().user_attendance

    def get_t_shirt_count(self):
        return PackageTransaction.objects.filter(team_package__box=self).count()

    def get_weight(self):
        """ Returns weight of this box """
        t_shirt_weight = self.delivery_batch.campaign.package_weight
        t_shirt_count = self.get_t_shirt_count()
        return t_shirt_weight * t_shirt_count

    def get_volume(self):
        campaign = self.delivery_batch.campaign
        t_shirt_volume = campaign.package_width * campaign.package_height * campaign.package_depth
        t_shirt_count = self.get_t_shirt_count()
        return t_shirt_volume * t_shirt_count


@receiver(post_save, sender=SubsidiaryBox)
def create_customer_sheets(sender, instance, created, **kwargs):
    if not instance.customer_sheets and getattr(instance, 'add_packages_on_save', True):
        with NamedTemporaryFile() as temp:
            customer_sheets.make_customer_sheets_pdf(temp, instance)
            instance.customer_sheets.save("customer_sheets_%s_%s.pdf" % (instance.pk, instance.created.strftime("%Y-%m-%d")), File(temp))
            instance.save()
