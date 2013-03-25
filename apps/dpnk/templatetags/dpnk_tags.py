from django import template
from django.conf import settings
register = template.Library()

from dpnk.wp_urls import wp_reverse

@register.simple_tag
def wp_url(name):
    return wp_reverse(name)

@register.simple_tag
def site_url():
    return settings.SITE_URL
