from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission

from model_mommy import mommy


class Permissions:
    def __init__(self, **kwargs):
        self.view_company = mommy.make(
            "auth.Permission",
            name="view_company",
            content_type=ContentType.objects.get(
                app_label="dpnk",
                model="company"
            ),
        )
        self.view_companyadmin = mommy.make(
            "auth.Permission",
            name="view_companyadmin",
            content_type=ContentType.objects.get(
                app_label="dpnk",
                model="companyadmin"
            ),
        )
        self.add_competition = mommy.make(
            "auth.Permission",
            name="add_competition",
            content_type=ContentType.objects.get(
                app_label="dpnk",
                model="competition"
            ),
        )
        self.delete_competition = mommy.make(
            "auth.Permission",
            name="delete_competition",
            content_type=ContentType.objects.get(
                app_label="dpnk",
                model="competition"
            ),
        )
        self.change_competition = mommy.make(
            "auth.Permission",
            name="change_competition",
            content_type=ContentType.objects.get(
                app_label="dpnk",
                model="competition"
            ),
        )
        self.view_competition = mommy.make(
            "auth.Permission",
            name="view_competition",
            content_type=ContentType.objects.get(
                app_label="dpnk",
                model="competition"
            ),
        )
        self.add_question = mommy.make(
            "auth.Permission",
            name="add_question",
            content_type=ContentType.objects.get(
                app_label="dpnk",
                model="question"
            ),
        )
        self.delete_question = mommy.make(
            "auth.Permission",
            name="delete_question",
            content_type=ContentType.objects.get(
                app_label="dpnk",
                model="question"
            ),
        )
        self.change_question = mommy.make(
            "auth.Permission",
            name="change_question",
            content_type=ContentType.objects.get(
                app_label="dpnk",
                model="question"
            ),
        )
        self.view_question = mommy.make(
            "auth.Permission",
            name="view_question",
            content_type=ContentType.objects.get(
                app_label="dpnk",
                model="question"
            ),
        )
        self.view_subsidiary = mommy.make(
            "auth.Permission",
            name="view_subsidiary",
            content_type=ContentType.objects.get(
                app_label="dpnk",
                model="subsidiary"
            ),
        )
        self.view_userattendance = mommy.make(
            "auth.Permission",
            name="view_userattendance",
            content_type=ContentType.objects.get(
                app_label="dpnk",
                model="userattendance"
            ),
        )
