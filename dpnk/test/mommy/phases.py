from model_mommy import mommy


class Competitions:
    def __init__(self, campaigns, **kwargs):
self.invoices = mommy.make(  # was pk=4
        "dpnk.phase",
        campaign = 339,
        phase_type = "invoices",
    )
    self.payment = mommy.make(  # was pk=3
        "dpnk.phase",
        campaign = 339,
        phase_type = "payment",
    )
    self.competition = mommy.make(  # was pk=2
        "dpnk.phase",
        campaign = 339,
        date_from = "2010-11-01",
        date_to = "2010-11-30",
        phase_type = "competition",
    )
    self.entry_enabled = mommy.make(  # was pk=7
        "dpnk.phase",
        campaign = 339,
        date_from = "2010-11-01",
        date_to = "2010-11-30",
        phase_type = "entry_enabled",
    )
    self.competition2009 = mommy.make(  # was pk=6
        "dpnk.phase",
        campaign = 338,
        date_from = "2009-12-01",
        date_to = "2009-12-30",
        phase_type = "competition",
    )
    self.entry_enabled2009 = mommy.make(  # was pk=8
        "dpnk.phase",
        campaign = 338,
        date_from = "2009-12-01",
        date_to = "2009-12-30",
        phase_type = "entry_enabled",
    )

