# -*- coding: utf-8 -*-

# Author: Petr Dlouhý <petr.dlouhy@auto-mat.cz>
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
from django import template
from django.conf import settings
from django.template import Context
from django.template.loader import get_template
from cache_utils.decorators import cached
import slumber
register = template.Library()


@register.simple_tag
@cached(600)
def cyklistesobe(city_slug, order="created_at"):
    api = slumber.API("http://www.cyklistesobe.cz/api/")
    kwargs = {}
    if city_slug:
        kwargs['group'] = city_slug
    try:
        cyklistesobe = api.issues.get(order=order, count=1, **kwargs)
    except:
        cyklistesobe = None
    template = get_template("templatetags/cyklistesobe.html")
    context = Context({'cyklistesobe': cyklistesobe})
    return template.render(context)


@register.simple_tag
@cached(600)
def wp_news():
    url = "http://www.dopracenakole.net/"
    api = slumber.API(url)
    try:
        wp_feed = api.list.get(feed="content_to_backend", _post_type="post", count=10)
    except:
        return ""
    template = get_template("templatetags/wp_news.html")
    context = Context({'wp_feed': wp_feed})
    return template.render(context)


@register.simple_tag
@cached(600)
def wp_article(id):
    url = "http://www.dopracenakole.net/"
    api = slumber.API(url)
    try:
        wp_article = api.list.get(feed="content_to_backend", _post_type="page", _id=id)
    except:
        return ""
    return wp_article.values()[0]['content']


@register.simple_tag
def site_url():
    return settings.SITE_URL


@register.filter
def split(str, splitter):
        return str.split(splitter)


@register.filter
def times(count):
    return range(int(count))
