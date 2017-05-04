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

from django import forms
from django.contrib.gis.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

import secretballot

from unidecode import unidecode

from .competition import Competition
from .user_attendance import UserAttendance


class ChoiceType(models.Model):
    """Typ volby"""
    class Meta:
        verbose_name = _(u"Typ volby")
        verbose_name_plural = _(u"Typ volby")
        unique_together = (("competition", "name"),)

    competition = models.ForeignKey(
        Competition,
        null=False,
        blank=False,
    )
    name = models.CharField(
        verbose_name=_(u"Jméno"),
        unique=True,
        max_length=40,
        null=True,
    )
    universal = models.BooleanField(
        verbose_name=_(u"Typ volby je použitelný pro víc otázek"),
        default=False,
    )

    def __str__(self):
        return "%s" % self.name


class QuestionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)
        if hasattr(self, 'request') and not self.request.user.is_superuser:
            administrated_cities = self.request.user.userprofile.administrated_cities.all()
            campaign_slug = self.request.subdomain
            self.fields['competition'].queryset = Competition.objects.filter(city__in=administrated_cities, campaign__slug=campaign_slug).distinct()

        if hasattr(self.instance, 'competition'):
            self.fields['choice_type'].queryset = ChoiceType.objects.filter(Q(competition=self.instance.competition) | Q(universal=True))
        else:
            self.fields['choice_type'].queryset = ChoiceType.objects.filter(universal=True)


class Question(models.Model):

    class Meta:
        verbose_name = _(u"Anketní otázka")
        verbose_name_plural = _(u"Anketní otázky")
        ordering = ("order",)

    QTYPES = (
        ('text', _(u"Text")),
        ('choice', _(u"Výběr odpovědi")),
        ('multiple-choice', _(u"Výběr z více odpovědí")),
    )

    COMMENT_TYPES = (
        (None, _(u"Nic")),
        ('text', _(u"Text")),
        ('link', _(u"Odkaz")),
        ('one-liner', _(u"Jeden řádek textu")),
    )

    name = models.CharField(
        verbose_name=_(u"Jméno"),
        max_length=60,
        null=True,
        blank=True,
    )
    text = models.TextField(
        verbose_name=_(u"Otázka"),
        null=True,
        blank=True,
    )
    date = models.DateField(
        verbose_name=_(u"Den"),
        null=True,
        blank=True,
    )
    question_type = models.CharField(
        verbose_name=_(u"Typ"),
        choices=QTYPES,
        default='text',
        max_length=16,
        null=False,
    )
    comment_type = models.CharField(
        verbose_name=_(u"Typ komentáře"),
        choices=COMMENT_TYPES,
        default=None,
        max_length=16,
        blank=True,
        null=True,
    )
    with_attachment = models.BooleanField(
        verbose_name=_(u"Povolit přílohu"),
        default=False,
        null=False,
    )
    order = models.IntegerField(
        verbose_name=_(u"Pořadí"),
        null=True,
        blank=True,
    )
    competition = models.ForeignKey(
        Competition,
        verbose_name=_(u"Soutěž"),
        null=False,
        blank=False,
    )
    choice_type = models.ForeignKey(
        ChoiceType,
        verbose_name=_(u"Typ volby"),
        default=None,
        null=True,
        blank=True,
    )
    required = models.BooleanField(
        verbose_name=_(u"Povinná otázka"),
        default=True,
        null=False,
    )

    def __str__(self):
        return "%s" % (self.name or self.text)

    def with_answer(self):
        return self.comment_type or self.with_attachment or self.question_type != 'text' or self.choice_type is not None


class Choice(models.Model):

    class Meta:
        verbose_name = _(u"Nabídka k anketním otázce")
        verbose_name_plural = _(u"Nabídky k anketním otázkám")
        unique_together = (("choice_type", "text"),)
        ordering = ("order", )

    choice_type = models.ForeignKey(
        ChoiceType,
        verbose_name=_(u"Typ volby"),
        null=False,
        blank=False,
    )
    text = models.CharField(
        verbose_name=_(u"Nabídka"),
        max_length=250,
        db_index=True,
        null=False,
    )
    points = models.IntegerField(
        verbose_name=_(u"Body"),
        null=True,
        blank=True,
        default=None,
    )
    order = models.PositiveIntegerField(
        default=0,
        blank=False,
        null=False,
    )

    def __str__(self):
        return "%s" % self.text


def questionnaire_filename(instance, filename):
    return 'questionaire/%s/%s/%s' % (instance.question.competition.campaign.slug, instance.question.competition.slug, unidecode(filename))


class Answer(models.Model):
    """Odpověď"""
    class Meta:
        verbose_name = _(u"Odpověď")
        verbose_name_plural = _(u"Odpovědi")
        ordering = ('user_attendance__team__subsidiary__city', 'pk')
        unique_together = (("user_attendance", "question"),)

    user_attendance = models.ForeignKey(UserAttendance, null=True, blank=True)
    question = models.ForeignKey(Question, null=False)
    choices = models.ManyToManyField(
        Choice,
        blank=True,
    )
    comment = models.TextField(
        verbose_name=_(u"Komentář"),
        max_length=600,
        null=True, blank=True,
    )
    points_given = models.FloatField(
        null=True, blank=True, default=None,
    )
    comment_given = models.TextField(
        verbose_name=_("Hodnotitelský komentář"),
        null=True,
        blank=True,
    )
    attachment = models.FileField(
        upload_to=questionnaire_filename,
        max_length=600,
        blank=True,
    )

    def has_any_answer(self):
        return self.comment or self.choices.all() or self.attachment or self.points_given

    def str_choices(self):
        return ", ".join([choice.text for choice in self.choices.all()])

    def str_choices_ids(self):
        return ", ".join([(str(ch.pk)) for ch in self.choices.all()])

    # TODO: repair tests with this
    # def __str__(self):
    #      return "%s" % self.str_choices()


secretballot.enable_voting_on(Answer)


@receiver(post_save, sender=Answer)
def answer_post_save(sender, instance, **kwargs):
    from .. import results
    competition = instance.question.competition
    if competition.competitor_type == 'team':
        results.recalculate_result(competition, instance.user_attendance.team)
    elif competition.competitor_type == 'single_user' or competition.competitor_type == 'liberos':
        results.recalculate_result(competition, instance.user_attendance)
    elif competition.competitor_type == 'company':
        results.recalculate_result(competition, instance.user_attendance.company())
