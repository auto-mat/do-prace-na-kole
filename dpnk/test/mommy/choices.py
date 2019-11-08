from model_mommy import mommy


class Choices:
    def __init__(self, choice_types, **kwargs):
        self.yes = mommy.make(  # was pk=1
            "dpnk.choice",
            text="yes",
            points=10,
            choice_type=choice_types.yes_no,
        )

        self.no = mommy.make(  # was pk=2
            "dpnk.choice",
            text="no",
            points=3,
            choice_type=choice_types.yes_no,
        )
