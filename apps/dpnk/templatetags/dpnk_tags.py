from django import template
from django.conf import settings
from dpnk import util
from django.template import Context
from django.template.loader import get_template
import slumber
register = template.Library()

from dpnk.wp_urls import wp_reverse

@register.simple_tag
def wp_url(name):
    return wp_reverse(name)

@register.simple_tag
def cyklistesobe(city_slug):
    api = slumber.API("http://www.cyklistesobe.cz/issues/")
    kwargs = {}
    if city_slug:
        kwargs['group'] = city_slug
    cyklistesobe = api.list.get(order="vote_count", count=1, **kwargs)
    template = get_template("templatetags/cyklistesobe.html")
    context = Context({ 'cyklistesobe': cyklistesobe })
    return template.render(context)

@register.simple_tag
def site_url():
    return settings.SITE_URL


@register.filter
def split(str,splitter):
        return str.split(splitter)


@register.filter
def times(count):
    return range(int(count))
