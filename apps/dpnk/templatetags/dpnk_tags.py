from django import template
register = template.Library()

from dpnk.wp_urls import urls

@register.simple_tag
def wp_url(name):
    return urls[name]