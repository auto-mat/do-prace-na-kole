from model_mommy import mommy

class Trips:
    def __init__(self, userattendances, commute_modes, **kwargs):
        self.to_2010_11_1_ua1115 = mommy.make(  # was pk=101
            "dpnk.trip",
            direction = "trip_to",
            distance = 5,
            date = "2010-11-1",
            commute_mode = commute_modes.by_foot,
            user_attendance = userattendances.userattendance,
        )
        self.from_2010_11_1_ua1115 = mommy.make(  # was pk=103
            "dpnk.trip",
            direction = "trip_from",
            distance = 3,
            date = "2010-11-2",
            commute_mode = commute_modes.by_other_vehicle,
            user_attendance = userattendances.userattendance,
        )
        self.from_2010_11_14_ua1115_gpx = mommy.make(  # was pk=2
            "dpnk.trip",
            date = "2010-11-14",
            user_attendance = userattendances.userattendance,
            gpx_file = "modranska-rokle.gpx",
            track = "MULTILINESTRING((0 0,-1 1))",
            direction = "trip_from",
        )
        self.to_2010_11_14_ua1115 = mommy.make(  # was pk=102
            "dpnk.trip",
            user_attendance = userattendances.userattendance,
            date = "2015-11-12",
            commute_mode = commute_modes.bicycle,
            distance = 5.3,
            direction = "trip_to",
        )
        self.to_2009_11_1_ua1115 = mommy.make(  # was pk=3
            "dpnk.trip",
            date = "2009-11-1",
            user_attendance = userattendances.userattendance,
            direction = "trip_to",
            commute_mode = commute_modes.by_other_vehicle,
        )
