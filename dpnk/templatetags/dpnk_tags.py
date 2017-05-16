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

from django import template
from django.conf import settings
from django.core.urlresolvers import NoReverseMatch, Resolver404, resolve, reverse
from django.utils.translation import activate, get_language
from django.utils.translation import ugettext_lazy as _

import slumber

from .. import util

register = template.Library()
logger = logging.getLogger(__name__)


@register.inclusion_tag("templatetags/cyklistesobe.html")
def cyklistesobe(city_slug, order="created_at"):
    api = slumber.API("http://www.cyklistesobe.cz/api/")
    kwargs = {}
    if city_slug:
        kwargs['group'] = city_slug
    try:
        cyklistesobe = api.issues.get(order=order, per_page=5, page=0, **kwargs)
    except slumber.exceptions.SlumberBaseException:
        logger.exception(u'Error fetching cyklistesobe page')
        cyklistesobe = None
    return {'cyklistesobe': cyklistesobe}


@register.inclusion_tag("templatetags/wp_news.html")
def wp_news(campaign, city=None):
    return _wp_news(
        campaign,
        _connected_to=city.slug if city else None,
        order="DESC",
        orderby="DATE",
        count=5,
        _year=util.today().year,
        header=_("Novinky"),
        city=city,
        **({} if city else {'_global_news': 1}),
    )


@register.inclusion_tag("templatetags/wp_news.html")
def wp_actions(campaign, city=None):
    return _wp_news(
        campaign,
        "locations",
        _("akce"),
        unfold="first",
        _page_subtype="event",
        _post_parent=city.slug if city else None,
        orderby='start_date',
        _year=util.today().year,
        count=5,
        header=_("Akce"),
        city=city,
    )


@register.inclusion_tag("templatetags/wp_news.html")
def wp_prize(campaign, city=None):
    return _wp_news(
        campaign,
        "locations",
        _("cena"),
        unfold="all",
        count=8,
        show_description=False,
        _page_subtype="prize",
        _post_parent=city.slug if city else None,
        order="ASC",
        orderby="menu_order",
        header=_("Ceny"),
        city=city,
    )


def _wp_news(
        campaign,
        post_type="post",
        post_type_string=_("novinka"),
        unfold="first",
        count=-1,
        show_description=True,
        orderby='published',
        reverse=True,
        header=None,
        city=None,
        **other_args
):
    get_params = {}
    get_params['feed'] = "content_to_backend"
    get_params['_post_type'] = post_type
    get_params['_number'] = count
    get_params['orderby'] = orderby
    get_params.update(other_args)
    url = campaign.wp_api_url
    api = slumber.API(url)
    try:
        wp_feed = api.feed.get(**get_params)
    except slumber.exceptions.SlumberBaseException:
        logger.exception(u'Error fetching wp news')
        return ""
    if not isinstance(wp_feed, list) and not isinstance(wp_feed, tuple):
        logger.exception('Error encoding wp news format', extra={'wp_feed': wp_feed})
        return ""
    return {
        'wp_feed': wp_feed,
        'post_type_string': post_type_string,
        'unfold': unfold,
        'show_description': show_description,
        'header': header,
        'city': city,
        'BASE_WP_URL': settings.BASE_WP_URL,
    }


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
        logger.exception(u'Error in change lang function', extra={'resolved_path': path})
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
