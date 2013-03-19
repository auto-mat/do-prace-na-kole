from django import template
register = template.Library()

from dpnk.wp_urls import wp_reverse

@register.simple_tag
def wp_url(name):
    return wp_reverse(name)