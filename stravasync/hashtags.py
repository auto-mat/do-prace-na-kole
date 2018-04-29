# -*- coding: utf-8 -*-
# Author: Timothy Hobbs <timothy <at> hobbs.cz>

directions = {
    'tam': 'trip_to',
    'zpet': 'trip_from',
    'zpět': 'trip_from',
    'there': 'trip_to',
    'back': 'trip_from',
}

hashtag_to_by_lang = {
    'cs': 'tam',
    'en': 'to',
}

hashtag_from_by_lang = {
    'cs': 'zpět',
    'en': 'from',
}


def get_hashtag_to(campaign_slug, lang):
    return build_hashtag(campaign_slug, hashtag_to_by_lang[lang])


def get_hashtag_from(campaign_slug, lang):
    return build_hashtag(campaign_slug, hashtag_from_by_lang[lang])


def build_hashtag(campaign_slug, direction):
    return '#' + campaign_slug + direction


class HashtagTable():
    def __init__(self, campaigns):
        self.hashtag_dict = {}
        for campaign in campaigns:
            for direction, dir_slug in directions.items():
                self.hashtag_dict[build_hashtag(campaign.slug, direction)] = (campaign, dir_slug)

    def get_campaign_and_direction(self, text):
        for hashtag, cdt in self.hashtag_dict.items():
            if hashtag in text:
                return cdt
        raise NoValidHashtagException()

    def get_campaign_and_direction_for_activity(self, activity):
        try:
            return self.get_campaign_and_direction(activity.name)
        except NoValidHashtagException as e:
            if activity.description:
                return self.get_campaign_and_direction(activity.description)
            else:
                raise NoValidHashtagException()


class NoValidHashtagException(Exception):
    pass
