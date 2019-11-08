from model_mommy import mommy


class TestResultsData:
    def __init__(self, campaigns, **kwargs):
        self.competition = mommy.make(  # was pk=0
            "dpnk.competition",
            campaign=campaigns.c2010,
            city=[],
            company=None,
            competitor_type="team",
            date_from="2013-05-01",
            date_to="2013-06-02",
            entry_after_beginning_days=7,
            is_public=True,
            name="Team frequency",
            public_answers=False,
            rules=None,
            sex=None,
            slug="TF",
            competition_type="frequency",
            url="http://www.dopracenakole.net/url/",
        )
