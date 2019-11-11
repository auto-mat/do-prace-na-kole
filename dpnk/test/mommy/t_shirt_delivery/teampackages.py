from model_mommy import mommy


class TeamPackages:
    def __init__(self, subsidiaryboxes, **kwargs):
        self.basic = mommy.make(  # was pk=7
            "t_shirt_delivery.teampackage",
            box=subsidiaryboxes.basic,
        )
