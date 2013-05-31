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

@register.filter(is_safe=True)
def percentage(value):
    if value and util.days_count() != 0:
        return (value / ((util.days_count()) * 2)) * 100
    else:
        return 0
