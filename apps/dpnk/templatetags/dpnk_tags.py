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
import html.parser
import logging

from cache_utils.decorators import cached

from django import template
from django.core.urlresolvers import NoReverseMatch, Resolver404, resolve, reverse
from django.template.loader import get_template
from django.utils.safestring import mark_safe
from django.utils.translation import activate, get_language
from django.utils.translation import ugettext_lazy as _

import slumber
register = template.Library()
logger = logging.getLogger(__name__)


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
    except slumber.exceptions.SlumberBaseException:
        logger.exception(u'Error fetching cyklistesobe page')
        cyklistesobe = None
    template = get_template("templatetags/cyklistesobe.html")
    context = {'cyklistesobe': cyklistesobe}
    return template.render(context)


@register.simple_tag
def wp_news(campaign, slug=None):
    return mark_safe(_wp_news_cached(campaign, slug, "news"))


@register.simple_tag
def wp_actions(campaign, slug=None):
    return mark_safe(_wp_news_cached(campaign, slug, "action"))


@register.simple_tag
def wp_prize(campaign, slug=None):
    return mark_safe(_wp_news_cached(campaign, slug, "prize"))


@cached(60 * 60)
def _wp_news_cached(campaign, slug=None, wp_type="news"):
    if wp_type == "action":
        return _wp_news(campaign, "locations", _("akce"), unfold="first", _page_subtype="event", _post_parent=slug, orderby='start_date')
    elif wp_type == "prize":
        return _wp_news(
            campaign, "locations", _("cena"), unfold="all", count=-1, show_description=False,
            _page_subtype="prize", _post_parent=slug, order="ASC", orderby="menu_order",
        )
    else:
        if slug:
            _global_news = {}
        else:
            _global_news = {'_global_news': 1}
        return _wp_news(campaign, _connected_to=slug, order="DESC", orderby="DATE", count=5, **_global_news)


def _wp_news(campaign, post_type="post", post_type_string=_("novinka"), unfold="first", count=-1, show_description=True, orderby='published', reverse=True, **other_args):
    get_params = {}
    get_params['feed'] = "content_to_backend"
    get_params['_post_type'] = post_type
    get_params['_number'] = count
    get_params.update(other_args)
    url = campaign.wp_api_url
    api = slumber.API(url)
    try:
        wp_feed = api.feed.get(**get_params)
    except slumber.exceptions.SlumberBaseException:
        logger.exception(u'Error fetching wp news')
        return ""
    template = get_template("templatetags/wp_news.html")
    context = {
        'wp_feed': wp_feed[:5],
        'post_type_string': post_type_string,
        'unfold': unfold,
        'show_description': show_description,
    }
    return template.render(context)


@register.simple_tag
def wp_article(campaign, article_id):
    return mark_safe(wp_article_cached(campaign, article_id))


@cached(60 * 60)
def wp_article_cached(campaign, article_id):
    url = campaign.wp_api_url
    api = slumber.API(url)
    try:
        wp_article = api.feed.get(feed="content_to_backend", _post_type="page", _id=id)
    except slumber.exceptions.SlumberBaseException:
        logger.exception(u'Error fetching wp article')
        return ""
    try:
        return wp_article[str(article_id)]['content']
    except KeyError:
        logger.exception(u'Bad wp article id')
        return ""


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
    except Resolver404:
        logger.exception(u'Error in change lang function')
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
