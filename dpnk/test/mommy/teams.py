import f
class Teams:
    def __init__(self, campaigns, subsidiaries, **kwargs):
        self.team = mommy.make(
            "dpnk.team",
            campaign = campaigns.campaign,
            subsidiary = subsidiaries.subsidiary,
            invitation_token = "token123213",
            name = "Testing team 1"
        )

        self.empty_team = mommy.make(
            "dpnk.team",
            campaign = campaigns.campaign,
            subsidiary = subsidiaries.subsidiary,
            invitation_token = "token123216",
            name = "Empty team",
        )

        self.team_other_subsidiary = mommy.make(
            "dpnk.team",
            campaign = campaigns.campaign,
            subsidiary = subsidiaries.other_subsidiary,
            invitation_token = "token123215",
            name = "Team in different subsidiary",
        )

        self.team_last_year = mommy.make(
            "dpnk.team",
            campaign = campaigns.campaign_2009,
            subsidiary = subsidiaries.other_subsidiary,
            invitation_token = "token123214",
            name = "Testing team last campaign",
        )
