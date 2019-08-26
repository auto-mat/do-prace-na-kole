from model_mommy import mommy


class Teams:
    def __init__(self, campaigns, subsidiaries, **kwargs):
        self.basic = mommy.make( #pk=1
            "dpnk.team",
            campaign = campaigns.c2010,
            subsidiary = subsidiaries.subsidiary,
            invitation_token = "token123213",
            name = "Testing team 1"
        )

        self.empty_team = mommy.make( #pk=4
            "dpnk.team",
            campaign = campaigns.c2010,
            subsidiary = subsidiaries.subsidiary,
            invitation_token = "token123216",
            name = "Empty team",
        )

        self.other_subsidiary = mommy.make( #pk=3
            "dpnk.team",
            campaign = campaigns.c2010,
            subsidiary = subsidiaries.other_subsidiary,
            invitation_token = "token123215",
            name = "Team in different subsidiary",
        )

        self.last_year = mommy.make( #pk=2
            "dpnk.team",
            campaign = campaigns.c2009,
            subsidiary = subsidiaries.other_subsidiary,
            invitation_token = "token123214",
            name = "Testing team last campaign",
        )
