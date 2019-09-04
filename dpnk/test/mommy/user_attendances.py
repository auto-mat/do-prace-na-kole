from model_mommy import mommy


class UserAttendances:
    def __init__(self, users, teams, tshirt_sizes, campaigns, **kwargs):
        self.userattendance = mommy.make(  # was pk=1115
            "dpnk.userattendance",
            approved_for_team = "approved",
            campaign = campaigns.campaign,
            created = "2015-11-12T18:18:40.223",
            distance = None,
            dont_want_insert_track = False,
            get_rides_count_denorm = 0,
            t_shirt_size = tshirt_sizes.basic,
            team = teams.basic,
            track = "MULTILINESTRING((0 0,-1 1))",
            updated = "2015-11-12T18:18:40.223",
            payment_status = "done",
            personal_data_opt_in = True,
            userprofile = users.userprofile,
        )
        self.userattendance2009 = mommy.make(  # was pk=1116
            "dpnk.userattendance",
            approved_for_team = "approved",
            campaign = campaigns.campaign_2009,
            created = "2015-11-12T18:18:40.223",
            distance = None,
            dont_want_insert_track = False,
            get_rides_count_denorm = 0,
            t_shirt_size = tshirt_sizes.basic,
            team = teams.last_year,
            track = "MULTILINESTRING((0 0,-1 1))",
            updated = "2015-11-12T18:18:40.223",
            personal_data_opt_in = True,
            userprofile = users.userprofile,
        )

        self.userattendance2 = mommy.make(  # was pk=1015
            "dpnk.userattendance",
            approved_for_team = "approved",
            campaign = campaigns.campaign,
            created = "2015-11-12T18:18:40.223",
            distance = None,
            dont_want_insert_track = False,
            get_rides_count_denorm = 0,
            t_shirt_size = None,
            team = teams.basic,
            track = "MULTILINESTRING((0 0,-1 1))",
            updated = "2015-11-12T18:18:40.223",
            payment_status = "done",
            personal_data_opt_in = True,
            userprofile = users.user2_userprofile,
        )

        self.null_userattendance = mommy.make(  # was pk=1016
        "dpnk.userattendance",
            approved_for_team = "approved",
            campaign = campaigns.campaign,
            created = "2015-11-12T18:18:40.223",
            distance = None,
            dont_want_insert_track = False,
            get_rides_count_denorm = 0,
            t_shirt_size = None,
            team = teams.other_subsidiary,
            track = None,
            updated = "2015-11-12T18:18:40.223",
            userprofile = users.null_user_profile,
        )

        self.whithout_team = mommy.make(  # was pk=3
            "dpnk.userattendance",
            approved_for_team = "undecided",
            campaign = campaigns.campaign,
            created = "2015-11-12T18:18:40.223",
            distance = None,
            dont_want_insert_track = False,
            get_rides_count_denorm = 0,
            t_shirt_size = None,
            team = None,
            track = None,
            updated = "2015-11-12T18:18:40.223",
            userprofile = users.user_without_team_userprofile,
        )

        self.unapproved_userattendance = mommy.make(  # was pk=5
            "dpnk.userattendance",
            approved_for_team = "undecided",
            campaign = campaigns.campaign,
            created = "2015-11-12T18:18:40.223",
            distance = None,
            dont_want_insert_track = False,
            get_rides_count_denorm = 0,
            t_shirt_size = None,
            team = teams.other_subsidiary,
            track = None,
            updated = "2015-11-12T18:18:40.223",
            userprofile = users.unapproved_user_userprofile,
        )

        self.todo_useraddendance_for_user_without_userattendance = mommy.make(  # was pk=1027
            "dpnk.userattendance",
            approved_for_team = "approved",
            campaign = campaigns.campaign_2009,
            created = "2015-11-12T18:18:40.223",
            distance = None,
            dont_want_insert_track = False,
            get_rides_count_denorm = 0,
            t_shirt_size = tshirt_sizes.basic,
            team = None,
            track = "MULTILINESTRING((0 0,-1 1))",
            updated = "2015-11-12T18:18:40.223",
            userprofile = users.user_without_userattendance_userprofile,
        )

        self.registered = mommy.make(  # was pk=2115
            "dpnk.userattendance",
            approved_for_team = "approved",
            campaign = campaigns.campaign,
            created = "2015-11-12T18:18:40.223",
            distance = None,
            dont_want_insert_track = False,
            get_rides_count_denorm = 0,
            t_shirt_size = tshirt_sizes.basic,
            team = teams.basic,
            track = "MULTILINESTRING((0 0,-1 1))",
            updated = "2015-11-12T18:18:40.223",
            payment_status = "done",
            personal_data_opt_in = True,
            userprofile = users.registered_user_userprofile,
        )
