import datetime
from itertools import cycle

from django.test import TestCase

from dpnk.test.mommy_recipes import UserAttendanceRecipe, testing_campaign

from model_mommy import mommy
from model_mommy.recipe import seq

from ..models.delivery_batch import generate_csv
from .. import wellpack_csv


class TestWellpackCsv(TestCase):
    def setUp(self):
        self.subsidiary_box_id = 55
        self.delivery_batch_id = 1
        t_shirt_size = mommy.make(
            "TShirtSize",
            name="Testing t-shirt size",
            campaign=testing_campaign,
            code="Testing t-shirt code",
            ship=True,
        )
        mommy.make(
            "price_level.PriceLevel",
            takes_effect_on=datetime.date(year=2017, month=1, day=1),
            pricable=testing_campaign,
        )
        user_attendances = UserAttendanceRecipe.make(
            campaign=testing_campaign,
            userprofile__user__username=seq("test_username "),
            userprofile__user__first_name="Testing",
            userprofile__user__email="foo@email.cz",
            userprofile__user__last_name=seq("User "),
            userprofile__nickname=cycle(["Nick", None]),
            userprofile__telephone=seq(123456789),
            t_shirt_size=t_shirt_size,
            transactions=[
                mommy.make(
                    "Payment",
                    status=99,
                    realized=datetime.date(year=2017, month=2, day=1),
                ),
            ],
            _quantity=5,
        )
        subsidiary_box = mommy.make(
            "SubsidiaryBox",
            id=self.subsidiary_box_id,
            subsidiary__address_street="Foo street",
            subsidiary__address_psc=12234,
            subsidiary__address_street_number="123",
            subsidiary__address_city="Foo city",
            subsidiary__address_recipient="Foo recipient",
            subsidiary__id=123,
            delivery_batch__campaign=testing_campaign,
        )
        mommy.make(
            "TeamPackage",
            box=subsidiary_box,
            team__users=user_attendances,
            team__name="Foo team with max name lenth fooo foo foo foo fooo",
            team__campaign=testing_campaign,
            team__subsidiary__company__name="Foo company",
            team__subsidiary__company__ico=1231321313,
            id=34567812,
            packagetransaction_set=mommy.make(
                "PackageTransaction",
                t_shirt_size=t_shirt_size,
                user_attendance=cycle(user_attendances),
                _quantity=1,
            ),
        )
        self.delivery_batch = mommy.make(
            "DeliveryBatch",
            id=self.delivery_batch_id,
            campaign=testing_campaign,
        )

    def test_make_wellpack_csv_file(self):
        generate_csv(
            file_name="delivery_batch",
            instance=self.delivery_batch,
            instance_field="wellpack_csv",
            generate_csv_func=wellpack_csv.generate_csv,
        )
        self.delivery_batch.save()
        with open(self.delivery_batch.wellpack_csv.path) as f:
            header = "ID dávky obj.,Číslo krabice,Testing t-shirt code\n"
            self.assertEqual(
                f.read(),
                f"{header}{self.delivery_batch_id},{self.subsidiary_box_id},1\n",
            )
