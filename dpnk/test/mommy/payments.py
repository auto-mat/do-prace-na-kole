from model_mommy import mommy


class Payments:
    def __init__(self, userattendances, **kwargs):
        self.klub_pratel = mommy.make(  # was pk=9
            "dpnk.payment",
            amount = 150,
            pay_type = "am",
            user_attendance = userattendances.registered,
            status = 1,
            created = "2015-1-01",
        )
        """
        self.bill = mommy.make(  # was pk=5
            "dpnk.payment",
            amount = 150,
            pay_type = "fc",
            trans_id = "2055-1",
            session_id = "2075-1J1455206453",
            transaction_ptr = transactions.new_2014,
        )
        self.t3 = mommy.make(  # was pk=3
            "dpnk.payment",
            amount = 150,
            trans_id = "2075-1",
            session_id = "2075-1J1455206433",
            transaction_ptr = transactions.no_status_ua1115,
        )
        self.t4 = mommy.make(  # was pk=4
            "dpnk.payment",
            amount = 145,
            pay_type = "fc",
            trans_id = "2075-2",
            session_id = "2075-1J1455206444",
            transaction_ptr = transactions.done_ua1115,
        )
        self.bill_t16 = mommy.make(  # was pk=16
            "dpnk.payment",
            amount = 145,
            pay_type = "fc",
            trans_id = "2075-2",
            session_id = "2075-1J145520666",
            transaction_ptr = transactions.done_ua1015,
        )
        self.bill_t17 = mommy.make(  # was pk=17
            "dpnk.payment",
            amount = 145,
            pay_type = "fc",
            trans_id = "2075-3",
            session_id = "2075-1J145520667",
            transaction_ptr = transactions.done_ua2115,
        )
        self.bill_t18 = mommy.make(  # was pk=18
            "dpnk.payment",
            amount = 145,
            pay_type = "fc",
            trans_id = "2075-3",
            session_id = "2075-1J145520668",
            transaction_ptr = transactions.done_ua1016,
        )"""
