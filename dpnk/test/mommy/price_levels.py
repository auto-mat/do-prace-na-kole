from model_mommy import mommy


class PriceLevels:
    def __init__(self, campaigns, companies, commute_modes, **kwargs):
        self.basic = mommy.make(  # was pk=1
            "price_level.PriceLevel",
            pricable = 339,
            takes_effect_on = "2000-1-01",
            price = 120,
            category = "basic",
        )

        self.company = mommy.make(  # was pk=2
            "price_level.PriceLevel",
            pricable = 339,
            takes_effect_on = "2000-1-01",
            price = 130,
            category = "company",
        )

        self.basic2011 = mommy.make(  # was pk=3
            "price_level.PriceLevel",
            pricable = 339,
            takes_effect_on = "2011-1-01",
            price = 210,
            category = "basic",
        )
        self.companty2011 = mommy.make(  # was pk=4
            "price_level.PriceLevel",
            pricable = 339,
            takes_effect_on = "2011-1-01",
            price = 230,
            category = "company",
        )

