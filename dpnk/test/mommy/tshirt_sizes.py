from model_mommy import mommy

class TshirtSizes:
    def __init__(self, campaigns, **kwargs)
        self.tshirt_size = mommy.make(
            "t_shirt_delivery.tshirtsize",
            campaign = campaigns.campaign,
            name = "Testing t-shirt size",
        )

        self.tshirt_size_with_price = mommy.make(
            "t_shirt_delivery.tshirtsize",
            campaign = campaigns.campaign,
            price = 100,
            name = "Testing t-shirt size with price",
        )
