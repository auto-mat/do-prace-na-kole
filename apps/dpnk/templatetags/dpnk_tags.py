from django import template
from django.conf import settings
from dpnk import util
register = template.Library()

from dpnk.wp_urls import wp_reverse

@register.simple_tag
def wp_url(name):
    return wp_reverse(name)

@register.simple_tag
def site_url():
    return settings.SITE_URL


@register.filter
def split(str,splitter):
        return str.split(splitter)


@register.filter
def times(count):
    return range(int(count))
