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
from django.template.loader import get_template
from cache_utils.decorators import cached
from django.utils.safestring import mark_safe
from django.core.urlresolvers import resolve, reverse
from django.utils.translation import activate, get_language
from django.utils.translation import ugettext_lazy as _
import slumber
register = template.Library()


@register.simple_tag
def cyklistesobe(city_slug, order="created_at"):
    return mark_safe(cyklistesobe_cached(city_slug, order))


@cached(600)
def cyklistesobe_cached(city_slug, order="created_at"):
    api = slumber.API("http://www.cyklistesobe.cz/api/")
    kwargs = {}
    if city_slug:
        kwargs['group'] = city_slug
    try:
        cyklistesobe = api.issues.get(order=order, per_page=5, page=0, **kwargs)
    except:
        cyklistesobe = None
    template = get_template("templatetags/cyklistesobe.html")
    context = {'cyklistesobe': cyklistesobe}
    return template.render(context)


@register.simple_tag
def wp_news(slug=None):
    return mark_safe(wp_news_cached(_connected_to=slug))


@register.simple_tag
def wp_actions(slug=None):
    return mark_safe(wp_news_cached("locations", _("akce"), False, _page_subtype="event", _post_parent=slug))


@register.simple_tag
def wp_prize(slug=None):
    return mark_safe(wp_news_cached("locations", _("cena"), True, _page_subtype="prize", _post_parent=slug, order="RAND"))


@cached(600)
def wp_news_cached(post_type="post", post_type_string=_("novinka"), unfold_first=True, **other_args):
    get_params = {}
    get_params['feed'] = "content_to_backend"
    get_params['_post_type'] = post_type
    get_params['_number'] = 5
    get_params.update(other_args)
    print(get_params)
    url = "http://www.dopracenakole.cz/"
    api = slumber.API(url)
    try:
        wp_feed = api.feed.get(**get_params)
    except:
        return ""
    template = get_template("templatetags/wp_news.html")
    context = {
        'wp_feed': wp_feed,
        'post_type_string': post_type_string,
        'unfold_first': unfold_first,
    }
    return template.render(context)


@register.simple_tag
def wp_article(id):
    return mark_safe(wp_article_cached(id))


@cached(600)
def wp_article_cached(id):
    url = "http://www.dopracenakole.cz/"
    api = slumber.API(url)
    try:
        wp_article = api.feed.get(feed="content_to_backend", _post_type="page", _id=id)
    except:
        return ""
    return wp_article[str(id)]['content']


@register.simple_tag
def site_url():
    return settings.SITE_URL


@register.filter
def split(str, splitter):
        return str.split(splitter)


@register.filter
def times(count):
    return range(int(count))


@register.simple_tag(takes_context=True)
def change_lang(context, lang=None, *args, **kwargs):
    """
    Get active page's url by a specified language
    Usage: {% change_lang 'en' %}
    """
    if 'request' not in context:
        return "/%s" % lang

    path = context['request'].path
    try:
        url_parts = resolve(path)
    except:
        return "/%s" % lang

    url = path
    cur_language = get_language()
    try:
        activate(lang)
        url = reverse(url_parts.view_name, kwargs=url_parts.kwargs)
    finally:
        activate(cur_language)

    return "%s" % url
