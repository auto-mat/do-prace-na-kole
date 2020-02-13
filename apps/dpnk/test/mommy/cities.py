from model_mommy import mommy


class Cities():
    def __init__(self, **kwargs):
        self.city = mommy.make(  # was pk=1
            "dpnk.city",
            slug="testing-city",
            cyklistesobe_slug="testing-city",
            name="Testing city",
        )

        self.other_city = mommy.make(  # was pk=2
            "dpnk.city",
            slug="other-city",
            cyklistesobe_slug="other-city",
            name="Other city",
        )
