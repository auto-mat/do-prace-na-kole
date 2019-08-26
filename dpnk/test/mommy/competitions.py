from model_mommy import mommy


class Competitions:
    def __init__(self, campaigns, companies, commute_modes, **kwargs):
        self.c2010_competition_individual_frequency = mommy.make(
            campaign = campaigns.campaign,
            city = [],
            company = companies.company,
            competitor_type = "single_user",
            date_from = "2010-11-01",
            date_to = "2010-11-15",
            entry_after_beginning_days = 7,
            is_public = True,
            name = "Pravidelnost jednotlivců",
            public_answers = False,
            rules = None,
            sex = None,
            slug = "pravidelnost-jednotlivcu",
            competition_type = "frequency",
            minimum_rides_base = 23,
            url = "http://www.dopracenakole.net/url/",
            commute_modes = [commute_modes.bicycle, commute_modes.by_foot],
        )
