from model_mommy import mommy


class Campaigns:
    def __init__(self, campaign_types, **kwargs):
        self.c2009 = mommy.make(  # pk = 338 in old fixtures
            'dpnk.Campaign',
            benefitial_admission_fee=350.0,
            benefitial_admission_fee_company=450.0,
            email_footer="",
            free_entry_cases_html="",
            invoice_sequence_number_first=1,
            invoice_sequence_number_last=999999999,
            mailing_list_enabled=None,
            mailing_list_id="12345abcde",
            minimum_percentage=66,
            minimum_rides_base=25,
            year=2009,
            package_depth=35,
            package_height=1,
            package_weight=0.25,
            package_width=26,
            previous_campaign=None,
            slug="testing-campaign-ly",
            tracking_number_first=0,
            tracking_number_last=999999999,
            campaign_type=campaign_types.basic,
        )

        self.c2010 = mommy.make(  # pk = 339 in old fixtures
            'dpnk.Campaign',
            benefitial_admission_fee=350.0,
            benefitial_admission_fee_company=450.0,
            email_footer="",
            free_entry_cases_html="",
            invoice_sequence_number_first=1,
            invoice_sequence_number_last=999999999,
            mailing_list_enabled=None,
            mailing_list_id="12345abcde",
            minimum_percentage=66,
            year=2010,
            minimum_rides_base=25,
            package_depth=35,
            package_height=1,
            package_weight=0.25,
            package_width=26,
            previous_campaign=self.c2009,
            campaign_type=campaign_types.basic,
            slug="testing-campaign",
            tracking_number_first=1111111,
            tracking_number_last=999999999,
            trip_plus_distance=5,
        )
