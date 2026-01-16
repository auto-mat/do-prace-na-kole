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
from django.urls import reverse, translate_url
from django.utils.formats import get_format
from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _

import requests

import slumber

from dpnk.util import get_all_logged_in_users

register = template.Library()
logger = logging.getLogger(__name__)

# https://stackoverflow.com/questions/41295142/is-there-a-way-to-globally-override-requests-timeout-setting/47384155#47384155
HTTP_TIMEOUT = 5.000


class TimeoutRequestsSession(requests.Session):
    def request(self, *args, **kwargs):
        if kwargs.get("timeout") is None:
            kwargs["timeout"] = HTTP_TIMEOUT
        return super(TimeoutRequestsSession, self).request(*args, **kwargs)


@register.inclusion_tag("templatetags/cyklistesobe.html")
def cyklistesobe(city_slug, order="created_at"):
    api = slumber.API(
        "http://www.cyklistesobe.cz/api/", session=TimeoutRequestsSession()
    )
    kwargs = {}
    if city_slug:
        kwargs["group"] = city_slug
    try:
        cyklistesobe = api.issues.get(order=order, per_page=5, page=0, **kwargs)
    except (
        slumber.exceptions.SlumberBaseException,
        requests.exceptions.RequestException,
    ):
        logger.exception("Error fetching cyklistesobe page")
        cyklistesobe = None
    return {"cyklistesobe": cyklistesobe}


@register.inclusion_tag("templatetags/wp_news.html")
def wp_news(campaign, city=None):
    return _wp_news(
        campaign,
        _connected_to=city.slug if city else None,
        order="DESC",
        orderby="DATE",
        count=5,
        _from=campaign.wp_api_date_from,
        header=_("Novinky"),
        city=city,
        **({} if city else {"_global_news": 1}),
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
        orderby="start_date",
        _from=campaign.wp_api_date_from,
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
        _from=campaign.wp_api_date_from,
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
    orderby="published",
    reverse=True,
    header=None,
    city=None,
    **other_args,
):
    get_params = {}
    get_params["feed"] = "content_to_backend"
    get_params["_post_type"] = post_type
    get_params["_number"] = count
    get_params["orderby"] = orderby
    get_params.update(other_args)
    url = campaign.campaign_type.wp_api_url
    api = slumber.API(url, session=TimeoutRequestsSession())
    try:
        wp_feed = api.feed.get(**get_params)
    except (
        slumber.exceptions.SlumberBaseException,
        requests.exceptions.RequestException,
    ):
        logger.exception("Error fetching wp news")
        return {}
    if not isinstance(wp_feed, list) and not isinstance(wp_feed, tuple):
        logger.exception("Error encoding wp news format", extra={"wp_feed": wp_feed})
        return {}
    return {
        "wp_feed": wp_feed,
        "post_type_string": post_type_string,
        "unfold": unfold,
        "show_description": show_description,
        "header": header,
        "city": city,
        "BASE_WP_URL": url,
    }


@register.simple_tag(takes_context=True)
def change_lang(context, lang=None, *args, **kwargs):
    """
    Get active page's url by a specified language
    Usage: {% change_lang 'en' %}
    """
    if "request" not in context:
        return "/%s" % lang

    path = context["request"].path
    return translate_url(path, lang)


@register.simple_tag(takes_context=True)
def campaign_base_url(context, campaign):
    if hasattr(campaign, "get_base_url"):
        return campaign.get_base_url(context["request"])


@register.simple_tag(takes_context=False)
def thousand_separator():
    return get_format("THOUSAND_SEPARATOR", get_language())


@register.simple_tag(takes_context=False)
def decimal_separator():
    return get_format("DECIMAL_SEPARATOR", get_language())


@register.filter
def unquote_html(value):
    html_parser = html.parser.HTMLParser()
    return html_parser.unescape(value)


@register.filter
def addstr(arg1, arg2):
    """concatenate arg1 & arg2"""
    return str(arg1) + str(arg2)


@register.filter
def round_number(value, decimal_places=1):
    try:
        return round(value, decimal_places)
    except TypeError:
        return value


@register.inclusion_tag("templatetags/logged_in_user_list.html")
def render_logged_in_user_list():
    users = get_all_logged_in_users()
    return {
        "users": ",<br> ".join(list(users.values_list("username", flat=True))),
        "users_count": users.count,
    }


@register.simple_tag
def concat_all(*args):
    """Concatenate all args"""
    return "".join(map(str, args))


@register.simple_tag
def concat_cities_into_url_param(user_profile):
    """Concatenate cities into URL city param value

    :param Object user_profile: UseProfile model instance

    :return str: URL city param with value &city=Praha&city=Brno...
    """
    cities = [
        f"&city={city}"
        for city in set(
            user_profile.administrated_cities.all().values_list("name", flat=True)
        )
    ]
    return "".join(cities)


@register.simple_tag(takes_context=True)
def get_app_base_url(context, url=None, url_params=None):
    """Get app base URL

    :param dict context: Django context
    :param str url: Django old frontend app router URL name for reverse func
    :param str url_params: Django old frontend app router URL params for reverse func
                           with following format e.g."token=X4NW6O067Z3THBYY91SFMZJ1D9EG4V,
                                                      initial_email=test@test.org"

    :return str: app base URL
    """
    rtwbb_frontend_app_base_url = getattr(settings, "RTWBB_FRONTEND_APP_BASE_URL", None)
    if rtwbb_frontend_app_base_url:
        if url:
            return f"{rtwbb_frontend_app_base_url}{url}"
        return rtwbb_frontend_app_base_url
    if url:
        params = {}
        if url_params:
            params = {
                k: v
                for k, v in (item.strip().split("=") for item in url_params.split(","))
            }
        return f"{context['absolute_uri']}{reverse(url, kwargs=params)}"
    return context["absolute_uri"]
