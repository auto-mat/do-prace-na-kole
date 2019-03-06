import datetime

from author.decorators import with_author

from django.contrib.gis.db import models
from django.utils.translation import ugettext_lazy as _


class DeadlineQuerySet(models.QuerySet):
    def forthcoming(self, campaign=None):
        return self.filter(campaign=campaign, deadline__gte=datetime.datetime.now()).earliest('deadline')


@with_author
class DeliveryBatchDeadline(models.Model):
    """Deadline dávky objednávek"""
    created = models.DateTimeField(
        verbose_name=_("Datum vytvoření"),
        default=datetime.datetime.now,
        null=False,
    )

    campaign = models.ForeignKey(
        'dpnk.Campaign',
        verbose_name=_("Kampaň"),
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )

    deadline = models.DateTimeField(
        null=False,
    )

    delivery_from = models.DateTimeField(
        null=True,
    )

    delivery_to = models.DateTimeField(
        null=True,
    )
    objects = models.Manager.from_queryset(DeadlineQuerySet)()

    class Meta:
        verbose_name = _("Deadline dávky objednávek")
        verbose_name_plural = _("Deadline dáveky objednávek")
