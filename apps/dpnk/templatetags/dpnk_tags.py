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
from cache_utils.decorators import cached
from django import template
from django.core.urlresolvers import resolve, reverse, NoReverseMatch
from django.template.loader import get_template
from django.utils.safestring import mark_safe
from django.utils.translation import activate, get_language
from django.utils.translation import ugettext_lazy as _
import html.parser
import slumber
register = template.Library()


@register.simple_tag
def cyklistesobe(city_slug, order="created_at"):
    return mark_safe(cyklistesobe_cached(city_slug, order))


@cached(60 * 60)
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
    return mark_safe(_wp_news_cached(slug, "news"))


@register.simple_tag
def wp_actions(slug=None):
    return mark_safe(_wp_news_cached(slug, "action"))


@register.simple_tag
def wp_prize(slug=None):
    return mark_safe(_wp_news_cached(slug, "prize"))


@cached(60 * 60)
def _wp_news_cached(slug=None, wp_type="news"):
    if wp_type == "action":
        return _wp_news("locations", _("akce"), unfold="first", _page_subtype="event", _post_parent=slug, sort_key='start_date')
    elif wp_type == "prize":
        return _wp_news("locations", _("cena"), unfold="all", count=-1, show_description=False, _page_subtype="prize", _post_parent=slug, order="ASC", orderby="menu_order")
    else:
        if slug:
            _global_news = {}
        else:
            _global_news = {'_global_news': 1}
        return _wp_news(_connected_to=slug, order="DESC", orderby="DATE", count=5, **_global_news)


def _wp_news(post_type="post", post_type_string=_("novinka"), unfold="first", count=-1, show_description=True, sort_key='published', reverse=True, **other_args):
    get_params = {}
    get_params['feed'] = "content_to_backend"
    get_params['_post_type'] = post_type
    get_params['_number'] = count
    get_params.update(other_args)
    url = "http://www.dopracenakole.cz/"
    api = slumber.API(url)
    try:
        wp_feed = api.feed.get(**get_params)
    except:
        return ""
    if len(wp_feed) > 0:
        wp_feed = sorted(wp_feed.values(), key=lambda item: item[sort_key], reverse=reverse)
    template = get_template("templatetags/wp_news.html")
    context = {
        'wp_feed': wp_feed[:5],
        'post_type_string': post_type_string,
        'unfold': unfold,
        'show_description': show_description,
    }
    return template.render(context)


@register.simple_tag
def wp_article(id):
    return mark_safe(wp_article_cached(id))


@cached(60 * 60)
def wp_article_cached(id):
    url = "http://www.dopracenakole.cz/"
    api = slumber.API(url)
    try:
        wp_article = api.feed.get(feed="content_to_backend", _post_type="page", _id=id)
    except:
        return ""
    return wp_article[str(id)]['content']


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
    except NoReverseMatch:
        pass
    finally:
        activate(cur_language)

    return "%s" % url


@register.filter
def unquote_html(value):
    html_parser = html.parser.HTMLParser()
    return html_parser.unescape(value)
