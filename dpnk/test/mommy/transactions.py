from django.contrib.contenttypes.models import ContentType

from model_mommy import mommy


class PackageTransactions:
    def __init__(self, userattendances, **kwargs):
        self.done = mommy.make(  # was pk=8
            "dpnk.transaction",
            user_attendance=userattendances.registered,
            status=99,
            created="2015-12-11T17:18:40.223",
            polymorphic_ctype=ContentType.objects.get(
                app_label="t_shirt_delivery",
                model="packagetransaction"
            ),
        )
        self.package_assembled_ua1115 = mommy.make(  # was pk=6
            "dpnk.transaction",
            user_attendance = userattendances.userattendance,
            status = 20003,
            created = "2015-11-12T18:18:40.223",
            polymorphic_ctype=ContentType.objects.get(
                app_label="t_shirt_delivery",
                model="packagetransaction"
            ),
        )
        self.packaged_assembled_ua3 = mommy.make(  # was pk=7
            "dpnk.transaction",
            user_attendance = userattendances.without_team,
            status = 20003,
            created = "2015-11-12T18:18:40.223",
            polymorphic_ctype=ContentType.objects.get(
                app_label="t_shirt_delivery",
                model="packagetransaction"
            ),
        )

class PaymentTransactions:
    def __init__(self, userattendances, **kwargs):
        self.new = mommy.make(  # was pk=9
            "dpnk.transaction",
            user_attendance = userattendances.registered,
            status = 1,
            created = "2015-1-01",
            polymorphic_ctype=ContentType.objects.get(
                app_label="dpnk",
                model="payment"
            ),
        )

        self.new_2014 = mommy.make(  # was pk=5
            "dpnk.transaction",
            user_attendance = userattendances.registered,
            status = 1,
            created = "2014-12-01",
            polymorphic_ctype=ContentType.objects.get(
                app_label="dpnk",
                model="payment"
            ),
        )

        self.no_status_ua1115 = mommy.make(  # was pk=3
            "dpnk.transaction",
            user_attendance = userattendances.userattendance,
            polymorphic_ctype=ContentType.objects.get(
                app_label="dpnk",
                model="payment"
            ),
        )

        self.done_ua1115 = mommy.make(  # was pk=4
            "dpnk.transaction",
            user_attendance = userattendances.userattendance,
            status = 99,
            realized = "2010-11-01",
            polymorphic_ctype=ContentType.objects.get(
                app_label="dpnk",
                model="payment"
            ),
        )

        self.done_ua1015 = mommy.make(  # was pk=16
            "dpnk.transaction",
            user_attendance = userattendances.userattendance2,
            status = 99,
            realized = "2010-11-01",
            polymorphic_ctype=ContentType.objects.get(
                app_label="dpnk",
                model="payment"
            ),
        )

        self.done_ua2115 = mommy.make(  # was pk=17
            "dpnk.transaction",
            user_attendance = userattendances.registered,
            status = 99,
            realized = "2010-11-01",
            polymorphic_ctype=ContentType.objects.get(
                app_label="dpnk",
                model="payment"
            ),
        )

        self.done_ua1016 = mommy.make(  # was pk=18
            "dpnk.transaction",
            user_attendance = userattendances.null_userattendance,
            status = 99,
            realized = "2010-11-01",
            polymorphic_ctype=ContentType.objects.get(
                app_label="dpnk",
                model="payment"
            ),
        )
