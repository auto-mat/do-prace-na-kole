from model_mommy import mommy


class SubsidiaryBoxes:
    def __init__(self, deliverybatches, **kwargs):
        self.basic = mommy.make(  # was pk=7
            "t_shirt_delivery.subsidiarybox", delivery_batch=deliverybatches.basic2,
        )
