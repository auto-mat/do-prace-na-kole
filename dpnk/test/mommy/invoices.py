from model_mommy import mommy

class Invoices:
    def __init__(self, campaigns, companies, **kwargs):
        self.basic = mommy.make(  # was pk=1
            "dpnk.invoice",
            company = companies.basic,
            campaign = campaigns.c2010,
            paid_date = "2010-10-10",
            sequence_number = 1,
        )
