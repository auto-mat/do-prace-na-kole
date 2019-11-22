from dpnk import util
from dpnk.models import UserAttendance

from model_mommy import mommy

from .suppress_autotime import suppress_autotime


class UserAttendances:
    def __init__(self, users, teams, tshirt_sizes, campaigns, **kwargs):
        with suppress_autotime(UserAttendance, ['created', 'updated']):
            self.userattendance = mommy.make(  # was pk=1115
                "dpnk.userattendance",
                approved_for_team="approved",
                campaign=campaigns.c2010,
                created="2015-11-12T18:18:40.223",
                get_rides_count_denorm=0,
                t_shirt_size=tshirt_sizes.basic,
                team=teams.basic,
                updated="2015-11-12T18:18:40.223",
                payment_status="done",
                personal_data_opt_in=True,
                userprofile=users.userprofile,
            )
            self.userattendance2009 = mommy.make(  # was pk=1116
                "dpnk.userattendance",
                approved_for_team="approved",
                campaign=campaigns.c2009,
                created="2015-11-12T18:18:40.223",
                get_rides_count_denorm=0,
                t_shirt_size=tshirt_sizes.basic,
                team=teams.last_year,
                updated="2015-11-12T18:18:40.223",
                personal_data_opt_in=True,
                userprofile=users.userprofile,
            )
            self.userattendance2 = mommy.make(  # was pk=1015
                "dpnk.userattendance",
                approved_for_team="approved",
                campaign=campaigns.c2010,
                created="2015-11-12T18:18:40.223",
                get_rides_count_denorm=0,
                t_shirt_size=None,
                team=teams.basic,
                updated="2015-11-12T18:18:40.223",
                payment_status="done",
                personal_data_opt_in=True,
                userprofile=users.user2_userprofile,
            )
            self.null_userattendance = mommy.make(  # was pk=1016
                "dpnk.userattendance",
                approved_for_team="approved",
                campaign=campaigns.c2010,
                created="2015-11-12T18:18:40.223",
                get_rides_count_denorm=0,
                t_shirt_size=None,
                team=teams.other_subsidiary,
                updated="2015-11-12T18:18:40.223",
                userprofile=users.null_userprofile,
            )
            self.whithout_team = mommy.make(  # was pk=3
                "dpnk.userattendance",
                approved_for_team="undecided",
                campaign=campaigns.c2010,
                created="2015-11-12T18:18:40.223",
                distance=None,
                get_rides_count_denorm=0,
                t_shirt_size=None,
                team=None,
                updated="2015-11-12T18:18:40.223",
                userprofile=users.user_without_team_userprofile,
            )
            self.unapproved_userattendance = mommy.make(  # was pk=5
                "dpnk.userattendance",
                approved_for_team="undecided",
                campaign=campaigns.c2010,
                created="2015-11-12T18:18:40.223",
                get_rides_count_denorm=0,
                t_shirt_size=None,
                team=teams.other_subsidiary,
                updated="2015-11-12T18:18:40.223",
                userprofile=users.unapproved_user_userprofile,
            )
            self.todo_useraddendance_for_user_without_userattendance = mommy.make(  # was pk=1027
                "dpnk.userattendance",
                approved_for_team="approved",
                campaign=campaigns.c2009,
                created="2015-11-12T18:18:40.223",
                get_rides_count_denorm=0,
                t_shirt_size=tshirt_sizes.basic,
                team=None,
                updated="2015-11-12T18:18:40.223",
                userprofile=users.user_without_userattendance_userprofile,
            )
            self.registered = mommy.make(  # was pk=2115
                "dpnk.userattendance",
                approved_for_team="approved",
                campaign=campaigns.c2010,
                created="2015-11-12T18:18:40.223",
                get_rides_count_denorm=0,
                t_shirt_size=tshirt_sizes.basic,
                team=teams.basic,
                updated="2015-11-12T18:18:40.223",
                payment_status="done",
                personal_data_opt_in=True,
                userprofile=users.registered_user_userprofile,
            )
        util.rebuild_denorm_models([self.userattendance, self.userattendance2])
