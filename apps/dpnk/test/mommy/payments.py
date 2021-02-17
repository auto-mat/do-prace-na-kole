from dpnk import util

from model_mommy import mommy


class Payments:
    def __init__(self, userattendances, teams, **kwargs):
        self.new_klub_pratel = mommy.make(  # was pk=9
            "dpnk.payment",
            amount=150,
            pay_type="am",
            user_attendance=userattendances.registered,
            status=1,
            created="2015-1-01",
        )
        self.new_bill_2014 = mommy.make(  # was pk=5
            "dpnk.payment",
            amount=150,
            pay_type="fc",
            trans_id="2055-1",
            session_id="2075-1J1455206453",
            user_attendance=userattendances.registered,
            status=1,
            created="2014-12-01",
        )
        self.no_status_ua1115 = mommy.make(  # was pk=3
            "dpnk.payment",
            amount=150,
            trans_id="2075-1",
            session_id="2075-1J1455206433",
            user_attendance=userattendances.userattendance,
        )
        self.done_bill_ua1115 = mommy.make(  # was pk=4
            "dpnk.payment",
            amount=145,
            pay_type="fc",
            trans_id="2075-2",
            session_id="2075-1J1455206444",
            user_attendance=userattendances.userattendance,
            status=99,
            realized="2010-11-01",
        )
        self.done_bill_ua1015 = mommy.make(  # was pk=16
            "dpnk.payment",
            amount=145,
            pay_type="fc",
            trans_id="2075-2",
            session_id="2075-1J145520666",
            user_attendance=userattendances.userattendance2,
            status=99,
            realized="2010-11-01",
        )
        self.done_bill_ua2115 = mommy.make(  # was pk=17
            "dpnk.payment",
            amount=145,
            pay_type="fc",
            trans_id="2075-3",
            session_id="2075-1J145520667",
            user_attendance=userattendances.registered,
            status=99,
            realized="2010-11-01",
        )
        self.done_bill_ua1016 = mommy.make(  # was pk=18
            "dpnk.payment",
            amount=145,
            pay_type="fc",
            trans_id="2075-3",
            session_id="2075-1J145520668",
            user_attendance=userattendances.null_userattendance,
            status=99,
            realized="2010-11-01",
        )
        util.rebuild_denorm_models(
            [
                userattendances.null_userattendance,
                userattendances.registered,
                userattendances.userattendance2,
                userattendances.userattendance,
            ]
        )
        util.rebuild_denorm_models(
            [
                teams.basic,
                teams.last_year,
                teams.other_subsidiary,
            ]
        )
