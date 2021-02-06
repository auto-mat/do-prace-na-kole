from django.contrib.auth.models import Permission


class Permissions:
    def __init__(self, **kwargs):
        self.view_company = Permission.objects.get(codename="view_company",)
        self.view_companyadmin = Permission.objects.get(codename="view_companyadmin",)
        self.add_competition = Permission.objects.get(codename="add_competition",)
        self.delete_competition = Permission.objects.get(codename="delete_competition",)
        self.change_competition = Permission.objects.get(codename="change_competition",)
        self.view_competition = Permission.objects.get(codename="view_competition",)
        self.add_question = Permission.objects.get(codename="add_question",)
        self.delete_question = Permission.objects.get(codename="delete_question",)
        self.change_question = Permission.objects.get(codename="change_question",)
        self.view_question = Permission.objects.get(codename="view_question",)
        self.view_subsidiary = Permission.objects.get(codename="view_subsidiary",)
        self.view_userattendance = Permission.objects.get(
            codename="view_userattendance",
        )
