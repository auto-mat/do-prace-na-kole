from model_mommy import mommy


class TshirtSizes:
    def __init__(self, campaigns, **kwargs):
        self.basic = mommy.make(  # pk=1
            "t_shirt_delivery.tshirtsize",
            campaign=campaigns.c2010,
            name="Testing t-shirt size",
        )
        self.with_price = mommy.make(  # pk=2
            "t_shirt_delivery.tshirtsize",
            campaign=campaigns.c2010,
            price=100,
            name="Testing t-shirt size with price",
        )
