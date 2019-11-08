from model_mommy import mommy


class CompanyAdmins:
    def __init__(self, users, campaigns, companies, **kwargs):
        self.company_admin = mommy.make(  # was pk=1
            "dpnk.companyadmin",
            userprofile=users.userprofile,
            can_confirm_payments=True,
            campaign=campaigns.c2010,
            administrated_company=companies.basic,
            company_admin_approved="approved",
        )
        self.company_admin2 = mommy.make(  # was pk=2
            "dpnk.companyadmin",
            userprofile=users.null_userprofile,
            can_confirm_payments=True,
            campaign=campaigns.c2010,
            administrated_company=companies.basic,
            company_admin_approved="approved",
        )
        self.company_admin_without_userattendance = mommy.make(  # was pk=3
            "dpnk.companyadmin",
            userprofile=users.user_without_userattendance_userprofile,
            can_confirm_payments=True,
            campaign=campaigns.c2010,
            administrated_company=companies.basic,
            company_admin_approved="approved",
        )
