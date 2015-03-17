from django import template
from django.conf import settings
from dpnk import util
from django.template import Context
from django.template.loader import get_template
from cache_utils.decorators import cached
import slumber
register = template.Library()

from dpnk.wp_urls import wp_reverse

@register.simple_tag
def wp_url(name):
    return wp_reverse(name)



@register.simple_tag
@cached(600)
def cyklistesobe(city_slug, order="created"):
    api = slumber.API("http://www.cyklistesobe.cz/issues/")
    kwargs = {}
    if city_slug:
        kwargs['group'] = city_slug
    try:
        cyklistesobe = api.list.get(order=order, count=1, **kwargs)
    except:
        cyklistesobe = None
    template = get_template("templatetags/cyklistesobe.html")
    context = Context({ 'cyklistesobe': cyklistesobe })
    return template.render(context)

@register.simple_tag
@cached(600)
def wp_news():
    url="http://www.dopracenakole.net/"
    api = slumber.API(url)
    try:
        wp_feed = api.list.get(feed="content_to_backend", _post_type="post", count=10)
    except:
        return ""
    template = get_template("templatetags/wp_news.html")
    context = Context({'wp_feed': wp_feed})
    return template.render(context)

@register.simple_tag
@cached(600)
def wp_article(id):
    url="http://www.dopracenakole.net/"
    api = slumber.API(url)
    try:
        wp_article = api.list.get(feed="content_to_backend", _post_type="page", _id=id)
    except:
        return ""
    return wp_article.values()[0]['content']

@register.simple_tag
def site_url():
    return settings.SITE_URL


@register.filter
def split(str,splitter):
        return str.split(splitter)


@register.filter
def times(count):
    return range(int(count))
