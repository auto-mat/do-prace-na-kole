from model_mommy import mommy


class CitiesInCampaign:
    def __init__(self, campaigns, cities, competitions, **kwargs):
        self.city_in_campaign = mommy.make(
            "dpnk.cityincampaign", city=cities.city, campaign=competitions.c2010,
        )
