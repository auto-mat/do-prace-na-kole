from model_mommy import mommy


class Transactions:
    def __init__(self, userattendances, **kwargs):

        self.done = mommy.make(  # was pk=8
            "dpnk.transaction",
            user_attendance = 2115,
            status = 99,
            created = "2015-12-11T17:18:40.223",
            polymorphic_ctype = ["t_shirt_delivery", "packagetransaction"],
        )

        self.new = mommy.make(  # was pk=9
            "dpnk.transaction",
            user_attendance = 2115,
            status = 1,
            created = "2015-1-01",
            polymorphic_ctype = ["dpnk", "payment"],
        )

    {
        "fields": {
            "user_attendance": 1115,
            "status": 20003,
            "created": "2015-11-12T18:18:40.223",
            "polymorphic_ctype": ["t_shirt_delivery", "packagetransaction"]
        },
        "model": "dpnk.transaction",
        "pk": 6
    },
    {
        "fields": {
            "user_attendance": 3,
            "status": 20003,
            "created": "2015-11-12T18:18:40.223",
            "polymorphic_ctype": ["t_shirt_delivery", "packagetransaction"]
        },
        "model": "dpnk.transaction",
        "pk": 7
    },
    {
        "fields": {
            "user_attendance": 2115,
            "status": 1,
            "created": "2014-12-01",
            "polymorphic_ctype": ["dpnk", "payment"]
        },
        "model": "dpnk.transaction",
        "pk": 5
    },
    {
        "fields": {
            "user_attendance": 1115,
            "polymorphic_ctype": ["dpnk", "payment"]
        },
        "model": "dpnk.transaction",
        "pk": 3
    },
    {
        "fields": {
            "user_attendance": 1115,
            "status": 99,
            "realized": "2010-11-01",
            "polymorphic_ctype": ["dpnk", "payment"]
        },
        "model": "dpnk.transaction",
        "pk": 4
    },
    {
        "fields": {
            "user_attendance": 1015,
            "status": 99,
            "realized": "2010-11-01",
            "polymorphic_ctype": ["dpnk", "payment"]
        },
        "model": "dpnk.transaction",
        "pk": 16
    },
    {
        "fields": {
            "user_attendance": 2115,
            "status": 99,
            "realized": "2010-11-01",
            "polymorphic_ctype": ["dpnk", "payment"]
        },
        "model": "dpnk.transaction",
        "pk": 17
    },
   {
        "fields": {
            "user_attendance": 1016,
            "status": 99,
            "realized": "2010-11-01",
            "polymorphic_ctype": ["dpnk", "payment"]
        },
        "model": "dpnk.transaction",
        "pk": 18
    },

