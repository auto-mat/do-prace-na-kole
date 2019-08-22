from dpnk import models
from model_mommy import mommy

def Fixtures():
    """
    Sets up a set of testing objects which are used throughout the test suit.

    Assumes that the commute_mode.json fixture is loaded.
    """
    def __init__(self):
        self.bicycle = models.CommuteMode.objects.get(pk=1)
        self.by_foot = models.CommuteMode.objects.get(pk=2)
        self.by_other_vehicle = models.CommuteMode.objects.get(pk=3)
        self.no_work = models.CommuteMode.objects.get(pk=4)

        self.campaign_type = mommy.make(
            'dpnk.CampaignType',
            name='Testing campaign',
        )

        self.campaign = mommy.make(
            'dpnk.Campaign',
            benefitial_admission_fee = 350.0,
            benefitial_admission_fee_company = 450.0,
            email_footer = "",
            free_entry_cases_html = "",
            invoice_sequence_number_first = 1,
            invoice_sequence_number_last = 999999999,
            mailing_list_enabled = None,
            mailing_list_id = "12345abcde",
            minimum_percentage = 66,
            year = 2010,
            minimum_rides_base = 25,
            name = "Testing campaign",
            package_depth = 35,
            package_height = 1,
            package_weight = 0.25,
            package_width = 26,
            previous_campaign = 338,
            campaign_type = self.campaign_type,
            slug = "testing-campaign",
            tracking_number_first = 1111111,
            tracking_number_last = 999999999,
            track_required = True,
            trip_plus_distance = 5,
        )

        self.campaign_2009 = mommy.make(
            'dpnk.Campaign',
            benefitial_admission_fee = 350.0,
            benefitial_admission_fee_company = 450.0,
            email_footer = "",
            free_entry_cases_html = "",
            invoice_sequence_number_first = 1,
            invoice_sequence_number_last = 999999999,
            mailing_list_enabled = None,
            mailing_list_id = "12345abcde",
            minimum_percentage = 66,
            minimum_rides_base = 25,
            name = "Testing campaign - last year",
            year = 2009,
            package_depth = 35,
            package_height = 1,
            package_weight = 0.25,
            package_width = 26,
            previous_campaign = None,
            slug = "testing-campaign-ly",
            tracking_number_first = 0,
            tracking_number_last = 999999999,
            campaign_type = self.campaign_type,
            track_required = True,
            trip_plus_distance = 5
        )

        self.c2010_registration_phase = mommy.make(
            'dpnk.Phase',
            campaign = self.campaign,
            date_from = "2010-11-01",
            date_to = "2010-11-30",
            phase_type = "registration",
        )

        self.c2010_competition_team_frequency = mommy.make(
            'dpnk.Competition',
            campaign = self.campaign,
            city = [],
            company = None,
            competitor_type = "team",
            date_from = "2010-11-01",
            date_to = "2010-11-15",
            entry_after_beginning_days = 7,
            is_public = True,
            name = "Pravidelnost týmů",
            public_answers = False,
            rules = None,
            sex = None,
            slug = "FQ-LB",
            competition_type = "frequency",
            minimum_rides_base = 23,
            url = "http://www.dopracenakole.net/url/",
            commute_modes = [self.bicycle, self.by_foot],
        )

        self.company = mommy.make(
            "dpnk.company",
            name = "Testing company",
            ico = "11111",
            dic = "CZ1234567890",
            address_psc = "11111",
            address_street_number = "1",
            address_street = "Ulice",
            address_city = "Praha",
        )

        self.company_no_admin = mommy.make(
            "dpnk.company",
            name = "Testing company without admin",
            ico = "11111",
            address_psc = "11111",
            address_street_number = "1",
            address_street = "Ulice",
            address_city = "Praha",
        )

        self.city = mommy.make(
            "dpnk.city",
            slug = "testing-city",
            cyklistesobe_slug = "testing-city",
            name = "Testing city",
        )

        self.other_city = mommy.make(
            "dpnk.city",
            slug = "other-city",
            cyklistesobe_slug = "other-city",
            name = "Other city"
        )

        self.city_in_campaign = mommy.make(
            "dpnk.cityincampaign",
            city = self.city,
            campaign = self.campaign_2009,
        )

        self.subsidiary = mommy.make(
            "dpnk.subsidiary",
            address_psc = "11111",
            address_street_number = "1",
            address_street = "Ulice",
            address_city = "Praha",
            company = self.company,
            city = self.city,
        )

        self.other_subsidiary = mommy.make(
            "dpnk.subsidiary",
            address_psc = "22222",
            address_street_number = "2",
            address_street = "Ulice",
            address_city = "Brno",
            company = self.company,
            city = self.other_city,
        )

        

        self.c2010_competition_individual_frequency = mommy.make(
            campaign = self.campaign,
            city = [],
            company = self.company,
            competitor_type = "single_user",
            date_from = "2010-11-01",
            date_to = "2010-11-15",
            entry_after_beginning_days = 7,
            is_public = True,
            name = "Pravidelnost jednotlivců",
            public_answers = False,
            rules = None,
            sex = None,
            slug = "pravidelnost-jednotlivcu",
            competition_type = "frequency",
            minimum_rides_base = 23,
            url = "http://www.dopracenakole.net/url/",
            commute_modes = [self.bicycle, self.by_foot],
        )
