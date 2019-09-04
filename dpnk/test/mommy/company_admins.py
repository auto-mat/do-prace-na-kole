from model_mommy import mommy


class CompanyAdmins:
    def __init__(self, users, campaigns, companies, **kwargs):
        self.company_admin = mommy.make(
            "dpnk.companyadmin",
            userprofile = users.userprofile,
            can_confirm_payments = True,
            campaign = campaigns.c2010,
            administrated_company = companies.basic,
            company_admin_approved = "approved",
        )

        self.company_admin2 = mommy.make(
            "dpnk.companyadmin",
            userprofile = users.null_user_profile,
            can_confirm_payments = True,
            campaign = "self.campaign",
            administrated_company = companies.basic,
            company_admin_approved = "approved",
        )
