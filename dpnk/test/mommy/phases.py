from datetime import date

from model_mommy import mommy


class Phases:
    def __init__(self, campaigns, **kwargs):
        self.invoices = mommy.make(  # was pk=4
            "dpnk.phase",
            campaign = campaigns.c2010,
            phase_type = "invoices",
        )
        self.payment = mommy.make(  # was pk=3
            "dpnk.phase",
            campaign = campaigns.c2010,
            phase_type = "payment",
        )
        self.competition = mommy.make(  # was pk=2
            "dpnk.phase",
            campaign = campaigns.c2010,
            date_from = date(2010, 11, 1),
            date_to = date(2010, 11, 30),
            phase_type = "competition",
        )
        self.entry_enabled = mommy.make(  # was pk=7
            "dpnk.phase",
            campaign = campaigns.c2010,
            date_from = date(2010, 11, 1),
            date_to = date(2010, 11, 30),
            phase_type = "entry_enabled",
        )
        self.registration_2010 = mommy.make(
            'dpnk.Phase',
            campaign = campaigns.c2010,
            date_from = date(2010, 11, 1),
            date_to = date(2010, 11, 30),
            phase_type = "registration",
        )
        self.competition2009 = mommy.make(  # was pk=6
            "dpnk.phase",
            campaign = campaigns.c2009,
            date_from = date(2009, 12, 1),
            date_to = date(2009, 12, 30),
            phase_type = "competition",
        )
        self.entry_enabled2009 = mommy.make(  # was pk=8
            "dpnk.phase",
            campaign = campaigns.c2009,
            date_from = date(2009, 12, 1),
            date_to = date(2009, 12, 30),
            phase_type = "entry_enabled",
        )
