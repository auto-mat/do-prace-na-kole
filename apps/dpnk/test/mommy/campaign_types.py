from model_mommy import mommy


class CampaignTypes:
    def __init__(self, **kwargs):
        self.basic = mommy.make("dpnk.CampaignType", name="Testing campaign",)
