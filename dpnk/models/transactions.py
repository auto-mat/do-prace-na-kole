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
import logging

from author.decorators import with_author

from denorm import denormalized, depend_on_related

from django.contrib.gis.db import models
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from polymorphic.models import PolymorphicModel

from .. import mailing
from ..email import payment_confirmation_company_mail, payment_confirmation_mail

logger = logging.getLogger(__name__)


class Status(object):
    NEW = 1
    CANCELED = 2
    REJECTED = 3
    COMMENCED = 4
    WAITING_CONFIRMATION = 5
    REJECTED = 7
    DONE = 99
    WRONG_STATUS = 888
    COMPANY_ACCEPTS = 1005
    INVOICE_MADE = 1006
    INVOICE_PAID = 1007
    FREE_FOR_PARTNER = 1008

    PACKAGE_NEW = 20001
    PACKAGE_ACCEPTED_FOR_ASSEMBLY = 20002
    PACKAGE_ASSEMBLED = 20003
    PACKAGE_SENT = 20004
    PACKAGE_DELIVERY_CONFIRMED = 20005
    PACKAGE_DELIVERY_DENIED = 20006
    PACKAGE_RECLAIM = 20007

    BIKE_REPAIR = 40001

    COMPETITION_START_CONFIRMED = 30002


PACKAGE_STATUSES = [
    (Status.PACKAGE_NEW, 'Nový'),
    (Status.PACKAGE_ACCEPTED_FOR_ASSEMBLY, 'Přijat k sestavení'),
    (Status.PACKAGE_ASSEMBLED, 'Sestaven'),
    (Status.PACKAGE_SENT, 'Odeslán'),
    (Status.PACKAGE_DELIVERY_CONFIRMED, 'Doručení potvrzeno'),
    (Status.PACKAGE_DELIVERY_DENIED, 'Dosud nedoručeno'),
    (Status.PACKAGE_RECLAIM, 'Reklamován'),
]

PAYMENT_STATUSES = [
    (Status.NEW, _(u'Nová')),
    (Status.CANCELED, _(u'Zrušena')),
    (Status.REJECTED, _(u'Odmítnuta')),
    (Status.COMMENCED, _(u'Zahájena')),
    (Status.WAITING_CONFIRMATION, _(u'Očekává potvrzení')),
    (Status.REJECTED, _(u'Platba zamítnuta, prostředky nemožno vrátit, řeší PayU')),
    (Status.DONE, _(u'Platba přijata')),
    (Status.WRONG_STATUS, _(u'Nesprávný status -- kontaktovat PayU')),
    (Status.COMPANY_ACCEPTS, _(u'Platba akceptována organizací')),
    (Status.FREE_FOR_PARTNER, _('Partner má startovné zdarma')),
    (Status.INVOICE_MADE, _(u'Faktura vystavena')),
    (Status.INVOICE_PAID, _(u'Faktura zaplacena')),
]

BIKE_REPAIR_STATUSES = [
    (Status.BIKE_REPAIR, 'Oprava v cykloservisu'),
]

COMPETITION_STATUSES = [
    (Status.COMPETITION_START_CONFIRMED, 'Potvrzen vstup do soutěže'),
]

STATUS = tuple(PACKAGE_STATUSES + PAYMENT_STATUSES + BIKE_REPAIR_STATUSES + COMPETITION_STATUSES)


@with_author
class Transaction(PolymorphicModel):
    """Transakce"""
    status = models.PositiveIntegerField(
        verbose_name=_(u"Status"),
        default=0,
        choices=STATUS,
        null=False,
        blank=False,
    )
    user_attendance = models.ForeignKey(
        'UserAttendance',
        related_name="transactions",
        null=True,
        blank=False,
        default=None,
        on_delete=models.CASCADE,
    )
    created = models.DateTimeField(
        verbose_name=_(u"Vytvoření"),
        default=datetime.datetime.now,
        null=False,
    )
    description = models.TextField(
        verbose_name=_(u"Popis"),
        null=True,
        blank=True,
        default="",
    )
    realized = models.DateTimeField(
        verbose_name=_(u"Realizace"),
        null=True, blank=True,
    )

    class Meta:
        verbose_name = _(u"Transakce")
        verbose_name_plural = _(u"Transakce")


class CommonTransaction(Transaction):
    """Obecná transakce"""

    class Meta:
        verbose_name = _(u"Obecná transakce")
        verbose_name_plural = _(u"Obecné transakce")


class UserActionTransaction(Transaction):
    """Uživatelská akce"""

    class Meta:
        verbose_name = _(u"Uživatelská akce")
        verbose_name_plural = _(u"Uživatelské akce")


class Payment(Transaction):
    """Platba"""

    done_statuses = [
        Status.DONE,
        Status.COMPANY_ACCEPTS,
        Status.FREE_FOR_PARTNER,
        Status.INVOICE_MADE,
        Status.INVOICE_PAID,
    ]
    waiting_statuses = [
        Status.NEW,
        Status.COMMENCED,
        Status.WAITING_CONFIRMATION,
    ]

    PAY_TYPES = (
        ('mp', _(u'mPenize - mBank')),
        ('kb', _(u'MojePlatba')),
        ('rf', _(u'ePlatby pro eKonto')),
        ('pg', _(u'GE Money Bank')),
        ('pv', _(u'Sberbank (Volksbank)')),
        ('pf', _(u'Fio banka')),
        ('cs', _(u'PLATBA 24 – Česká spořitelna')),
        ('era', _(u'Era - Poštovní spořitelna')),
        ('cb', _(u'ČSOB')),
        ('c', _(u'Kreditní karta přes GPE')),
        ('bt', _(u'bankovní převod')),
        ('pt', _(u'převod přes poštu')),
        ('sc', _(u'superCASH')),  # Deprecated
        ('psc', _(u'PaySec')),
        ('mo', _(u'Mobito')),
        ('uc', _(u'UniCredit')),
        ('t', _(u'testovací platba')),

        ('fa', _(u'faktura mimo PayU')),
        ('fc', _(u'organizace platí fakturou')),
        ('am', _(u'člen Klubu přátel Auto*Matu')),
        ('amw', _(u'kandidát na členství v Klubu přátel Auto*Matu')),
        ('fe', _('neplatí účastnický poplatek ')),
    )
    PAY_TYPES_DICT = dict(PAY_TYPES)

    NOT_PAYING_TYPES = [
        'am',
        'amw',
        'fe',
    ]

    PAYU_PAYING_TYPES = [
        'mp',
        'kb',
        'rf',
        'pg',
        'pv',
        'pf',
        'cs',
        'era',
        'cb',
        'c',
        'bt',
        'pt',
        'sc',
        'psc',
        'mo',
        'uc',
        't',
    ]

    class Meta:
        verbose_name = _(u"Platební transakce")
        verbose_name_plural = _(u"Platební transakce")

    order_id = models.CharField(
        verbose_name="Order ID",
        max_length=50,
        null=True,
        blank=True,
        default="",
    )
    session_id = models.CharField(
        verbose_name="Session ID",
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        default=None,
    )
    trans_id = models.CharField(
        verbose_name="Transaction ID",
        max_length=50, null=True, blank=True,
    )
    amount = models.PositiveIntegerField(
        verbose_name=_(u"Částka"),
        null=False,
    )
    pay_type = models.CharField(
        verbose_name=_(u"Typ platby"),
        choices=PAY_TYPES,
        max_length=50,
        null=True, blank=True,
    )
    error = models.PositiveIntegerField(
        verbose_name=_(u"Chyba"),
        null=True, blank=True,
    )
    invoice = models.ForeignKey(
        'Invoice',
        null=True,
        blank=True,
        default=None,
        on_delete=models.SET_NULL,
        related_name=("payment_set"),
    )

    # TODO: This is hack which allows making denorms dependend only on Payment and not on any other type of transaction.
    # Better would be to add some kind of conditions ti denorms
    @denormalized(models.ForeignKey, 'UserAttendance', null=True, blank=False, default=None, on_delete=models.CASCADE)
    @depend_on_related('Transaction', foreign_key='transaction_ptr', skip={'updated', 'created'})
    def payment_user_attendance(self):
        return self.user_attendance

    # TODO: This is hack which allows making denorms dependend only on Payment and not on any other type of transaction.
    # Better would be to add some kind of conditions ti denorms
    @denormalized(models.PositiveIntegerField, default=0, choices=STATUS, null=True, blank=True)
    @depend_on_related('Transaction', foreign_key='transaction_ptr', skip={'updated', 'created'})
    def payment_status(self):
        return self.status

    def payment_complete_date(self):
        if self.pay_type in ('am', 'amw'):
            return self.created
        else:
            return self.realized

    def save(self, *args, **kwargs):
        status_before_update = None
        if self.id:
            status_before_update = Payment.objects.get(pk=self.id).status
            logger.info(u"Saving payment (before): %s" % Payment.objects.get(pk=self.id).full_string())
        super().save(*args, **kwargs)

        statuses_company_ok = (Status.COMPANY_ACCEPTS, Status.INVOICE_MADE, Status.INVOICE_PAID)
        if (
                self.user_attendance and
                (status_before_update != Status.DONE) and
                self.status == Status.DONE):
            payment_confirmation_mail(self.user_attendance)
        elif (self.user_attendance and
                (status_before_update not in statuses_company_ok) and
                self.status in statuses_company_ok):
            payment_confirmation_company_mail(self.user_attendance)

        logger.info(u"Saving payment (after):  %s" % Payment.objects.get(pk=self.id).full_string())

    def full_string(self):
        if self.user_attendance:
            user = self.user_attendance
            username = self.user_attendance.userprofile.user.username
        else:
            user = None
            username = None
        return (
            "id: %s, "
            "user: %s (%s), "
            "order_id: %s, "
            "session_id: %s, "
            "trans_id: %s, "
            "amount: %s, "
            "description: %s, "
            "created: %s, "
            "realized: %s, "
            "pay_type: %s, "
            "status: %s, "
            "error: %s" % (
                self.pk,
                user,
                username,
                self.order_id,
                getattr(self, "session_id", ""),
                self.trans_id,
                self.amount,
                self.description,
                self.created,
                self.realized,
                self.pay_type,
                self.status,
                self.error,
            )
        )


@receiver(post_save, sender=UserActionTransaction)
@receiver(post_delete, sender=UserActionTransaction)
def update_user_attendance(sender, instance, *args, **kwargs):
    if not kwargs.get('raw', False):
        mailing.add_or_update_user(instance.user_attendance)


@receiver(post_save, sender=Payment)
def update_mailing_payment(sender, instance, created, **kwargs):
    if instance.user_attendance and kwargs.get('raw', False):
        mailing.add_or_update_user(instance.user_attendance)


@receiver(pre_save, sender=Payment)
def payment_set_realized_date(sender, instance, **kwargs):
    if instance.status in Payment.done_statuses and not instance.realized:
        instance.realized = datetime.datetime.now()
