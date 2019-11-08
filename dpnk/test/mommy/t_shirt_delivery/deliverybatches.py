from model_mommy import mommy


class DeliveryBatches:
    def __init__(self, campaigns, **kwargs):
        self.basic1 = mommy.make(  # was pk=1
            "t_shirt_delivery.deliverybatch",
            created="2015-11-12T18:18:40.223",
            campaign=campaigns.c2010,
        )
        self.basic2 = mommy.make(  # was pk=7
            "t_shirt_delivery.deliverybatch",
            campaign=campaigns.c2010,
        )
