# -*- coding: utf-8 -*-
# Author: Timothy Hobbs <timothy <at> hobbs.cz>
from dpnk.models.campaign import Campaign

directions = {
    'tam': 'trip_to',
    'zpet': 'trip_from',
    'there': 'trip_to',
    'back': 'trip_from',
}


class NoValidHashtagException(Exception):
    pass


def get_hashtags(title):
    words = title.split()
    broken_words = [x.split("#") for x in words]
    hash_tag_clumps = [x[1:] for x in broken_words if len(x) > 1]
    return [x for y in hash_tag_clumps for x in y]


def get_campaign_slug_and_direction(title):
    try:
        for hashtag in get_hashtags(title):
            for text, dir_slug in directions.items():
                if hashtag.endswith(text):
                    return hashtag[:-(len(text))], dir_slug
    except IndexError:
        raise NoValidHashtagException("No hashtags found.")
    raise NoValidHashtagException("No hashtags found.")


def get_campaign_and_direction(activity_title):
    campaing_slug, direction = get_campaign_slug_and_direction(activity_title)
    try:
        campaign = Campaign.objects.get(slug=campaing_slug)
    except Campaign.DoesNotExist:
        raise NoValidHashtagException("Campaign " + campaing_slug + " specified in hashtag does not exist.")
    return campaign, direction
