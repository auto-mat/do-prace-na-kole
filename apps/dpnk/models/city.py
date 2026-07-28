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

from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _

from .. import util


class City(models.Model):
    """Město"""

    class Meta:
        verbose_name = _("Město")
        verbose_name_plural = _("Města")
        ordering = ("name",)

    name = models.CharField(
        verbose_name=_("Jméno"),
        unique=True,
        max_length=40,
        null=False,
    )
    slug = models.SlugField(
        unique=True,
        verbose_name=_("Subdoména v URL"),
        blank=False,
    )
    wp_slug = models.SlugField(
        unique=True,
        verbose_name=_("Subdoména na WordPressu"),
        help_text=_("Pokud není vyplněno, použije se slug"),
        blank=True,
        null=True,
    )
    cyklistesobe_slug = models.SlugField(
        verbose_name=_("Jméno skupiny na webu Cyklisté sobě"),
        max_length=40,
        null=True,
    )
    location = models.PointField(
        verbose_name=_("poloha města"),
        srid=4326,
        null=True,
        blank=False,
    )

    def __str__(self):
        return "%s" % self.name

    def get_wp_slug(self):
        if self.wp_slug:
            return self.wp_slug
        return self.slug

    def get_wp_url(self):
        # TODO
        return "https://dopracenakole.cz/mesta/" + self.get_wp_slug()

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        if self.pk:
            for subsidiary in self.subsidiary_set.all():
                for team in subsidiary.teams.all():
                    for user in team.users.all():
                        if hasattr(user, "userprofile"):
                            # Delete REST API cache
                            cache = util.Cache(
                                key=f"{util.register_challenge_serializer_base_cache_key_name}"
                                f"{user.userprofile.id}:{user.campaign.slug}"
                            )
                            if cache.data:
                                del cache.data
        super().save(force_insert, force_update, *args, **kwargs)
