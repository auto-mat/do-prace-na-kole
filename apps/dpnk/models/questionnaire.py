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
from django.apps import apps
from django.contrib.gis.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

import secretballot

from .competition import Competition
from .user_attendance import UserAttendance


class ChoiceType(models.Model):
    """Typ volby"""

    class Meta:
        verbose_name = _("Typ volby")
        verbose_name_plural = _("Typ volby")
        unique_together = (("competition", "name"),)

    competition = models.ForeignKey(
        Competition,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )
    name = models.CharField(
        verbose_name=_("Jméno"),
        unique=True,
        max_length=40,
        null=True,
    )
    universal = models.BooleanField(
        verbose_name=_("Typ volby je použitelný pro víc otázek"),
        default=False,
    )

    def __str__(self):
        return "%s" % self.name


class QuestionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(self, "request") and not self.request.user.is_superuser:
            administrated_cities = (
                self.request.user.userprofile.administrated_cities.all()
            )
            campaign_slug = self.request.subdomain
            self.fields["competition"].queryset = Competition.objects.filter(
                city__in=administrated_cities, campaign__slug=campaign_slug
            ).distinct()

        if hasattr(self.instance, "competition"):
            self.fields["choice_type"].queryset = ChoiceType.objects.filter(
                Q(competition=self.instance.competition) | Q(universal=True)
            )
        else:
            self.fields["choice_type"].queryset = ChoiceType.objects.filter(
                universal=True
            )


class Question(models.Model):
    class Meta:
        verbose_name = _("Anketní otázka")
        verbose_name_plural = _("Anketní otázky")
        ordering = ("order",)

    QTYPES = (
        ("text", _("Text")),
        ("choice", _("Výběr odpovědi")),
        ("multiple-choice", _("Výběr z více odpovědí")),
    )

    COMMENT_TYPES = (
        (None, _("Nic")),
        ("text", _("Text")),
        ("link", _("Odkaz")),
        ("one-liner", _("Jeden řádek textu")),
    )

    name = models.CharField(
        verbose_name=_("Jméno"),
        max_length=60,
        null=True,
        blank=True,
    )
    text = models.TextField(
        verbose_name=_("Otázka"),
        null=True,
        blank=True,
    )
    date = models.DateField(
        verbose_name=_("Den"),
        null=True,
        blank=True,
    )
    question_type = models.CharField(
        verbose_name=_("Typ"),
        choices=QTYPES,
        default="text",
        max_length=16,
        null=False,
    )
    comment_type = models.CharField(
        verbose_name=_("Typ komentáře"),
        choices=COMMENT_TYPES,
        default=None,
        max_length=16,
        blank=True,
        null=True,
    )
    with_attachment = models.BooleanField(
        verbose_name=_("Povolit přílohu"),
        default=False,
        null=False,
    )
    order = models.IntegerField(
        verbose_name=_("Pořadí"),
        null=True,
        blank=True,
    )
    competition = models.ForeignKey(
        Competition,
        verbose_name=_("Soutěž"),
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )
    choice_type = models.ForeignKey(
        ChoiceType,
        verbose_name=_("Typ volby"),
        default=None,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    required = models.BooleanField(
        verbose_name=_("Povinná otázka"),
        default=True,
        null=False,
    )

    def __str__(self):
        return "%s" % (self.name or self.text)

    def with_answer(self):
        return (
            self.comment_type
            or self.with_attachment
            or self.question_type != "text"
            or self.choice_type is not None
        )


class Choice(models.Model):
    class Meta:
        verbose_name = _("Nabídka k anketním otázce")
        verbose_name_plural = _("Nabídky k anketním otázkám")
        unique_together = (("choice_type", "text"),)
        ordering = ("order",)

    choice_type = models.ForeignKey(
        ChoiceType,
        verbose_name=_("Typ volby"),
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )
    text = models.CharField(
        verbose_name=_("Nabídka"),
        max_length=250,
        db_index=True,
        null=False,
    )
    points = models.IntegerField(
        verbose_name=_("Body"),
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
    return "questionaire/dpnk-%s/%s/%s" % (
        instance.question.competition.campaign.pk,
        instance.question.competition.slug,
        slugify(filename),
    )


class Answer(models.Model):
    """Odpověď"""

    class Meta:
        verbose_name = _("Odpověď")
        verbose_name_plural = _("Odpovědi")
        ordering = ("user_attendance__team__subsidiary__city", "pk")
        unique_together = (("user_attendance", "question"),)

    user_attendance = models.ForeignKey(
        UserAttendance,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    question = models.ForeignKey(
        Question,
        null=False,
        on_delete=models.CASCADE,
    )
    choices = models.ManyToManyField(
        Choice,
        blank=True,
    )
    comment = models.TextField(
        verbose_name=_("Komentář"),
        max_length=600,
        null=True,
        blank=True,
    )
    points_given = models.FloatField(
        null=True,
        blank=True,
        default=None,
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
        return (
            self.comment or self.choices.all() or self.attachment or self.points_given
        )

    def str_choices(self):
        return ", ".join([choice.text for choice in self.choices.all()])

    def str_choices_ids(self):
        return ", ".join([(str(ch.pk)) for ch in self.choices.all()])

    @classmethod
    def export_resource_classes(cls):
        from .. import resources

        return {
            "Answers": ("Answers", resources.AnswerResource),
        }

    # TODO: repair tests with this
    # def __str__(self):
    #      return "%s" % self.str_choices()


if apps.ready:
    secretballot.enable_voting_on(Answer)


@receiver(post_save, sender=Answer)
def answer_post_save(sender, instance, **kwargs):
    from .. import results

    competition = instance.question.competition
    if competition.competitor_type == "team":
        results.recalculate_result(competition, instance.user_attendance.team)
    elif (
        competition.competitor_type == "single_user"
        or competition.competitor_type == "liberos"
    ):
        results.recalculate_result(competition, instance.user_attendance)
    elif competition.competitor_type == "company":
        results.recalculate_result(competition, instance.user_attendance.company())
