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
import datetime
from io import StringIO

from author.decorators import with_author

import denorm

from django.contrib.gis.db import models
from django.core.files import File
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from dpnk.models import Subsidiary

from .package_transaction import Status
from .. import batch_csv


@with_author
class DeliveryBatch(models.Model):
    """Dávka objednávek"""

    created = models.DateTimeField(
        verbose_name=_(u"Datum vytvoření"),
        default=datetime.datetime.now,
        null=False,
    )
    campaign = models.ForeignKey(
        'dpnk.Campaign',
        verbose_name=_(u"Kampaň"),
        null=False,
        blank=False,
    )
    customer_sheets = models.FileField(
        verbose_name=_(u"Zákaznické listy"),
        upload_to=u'customer_sheets',
        blank=True,
        null=True,
    )
    tnt_order = models.FileField(
        verbose_name=_(u"CSV objednávka"),
        upload_to=u'csv_delivery',
        blank=True,
        null=True,
    )
    dispatched = models.BooleanField(
        verbose_name=_("Vyřízeno"),
        blank=False,
        null=False,
        default=False,
    )

    class Meta:
        verbose_name = _(u"Dávka objednávek")
        verbose_name_plural = _(u"Dávky objednávek")

    def __str__(self):
        return "id %s vytvořená %s" % (self.id, self.created.strftime("%Y-%m-%d %H:%M:%S"))

    def box_count(self):
        return self.subsidiarybox_set.count()

    @transaction.atomic
    def add_packages(self, user_attendances=None):
        from .team_package import TeamPackage
        from .package_transaction import PackageTransaction
        from .subsidiary_box import SubsidiaryBox
        if not user_attendances:
            user_attendances = self.campaign.user_attendances_for_delivery()
        for subsidiary in Subsidiary.objects.filter(teams__users__in=user_attendances).distinct():
            subsidiary_box = SubsidiaryBox.objects.create(
                delivery_batch=self,
                subsidiary=subsidiary,
            )
            for team in subsidiary.teams.filter(users__in=user_attendances).distinct():
                team_package = TeamPackage(
                    box=subsidiary_box,
                    team=team,
                )
                team_package.add_packages_on_save = True
                team_package.save()
                for user_attendance in user_attendances.distinct() & team.users.distinct():
                    PackageTransaction.objects.create(
                        team_package=team_package,
                        user_attendance=user_attendance,
                        status=Status.PACKAGE_ACCEPTED_FOR_ASSEMBLY,
                    )
                team_package.add_packages_on_save = True
                team_package.save()
            denorm.flush()


@receiver(post_save, sender=DeliveryBatch)
def create_delivery_files(sender, instance, created, **kwargs):
    if created and getattr(instance, 'add_packages_on_save', True):
        instance.add_packages()

    if not instance.tnt_order and getattr(instance, 'add_packages_on_save', True):
        temp = StringIO()
        batch_csv.generate_csv(temp, instance)
        instance.tnt_order.save("delivery_batch_%s_%s.csv" % (instance.pk, instance.created.strftime("%Y-%m-%d")), File(temp))
        instance.save()
