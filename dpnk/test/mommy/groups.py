from model_mommy import mommy


class Groups:
    def __init__(self, permissions, **kwargs):
        self.cykloservis_group = mommy.make(  # was pk=5
            "auth.group",
            name="cykloservis",
        )

        self.local_organizer_group = mommy.make(  # was pk=4
            "auth.group",
            name="mistni koordinator",
        )
        self.local_organizer_group.permissions.set(
            [
                permissions.view_company,
                permissions.view_companyadmin,
                permissions.add_competition,
                permissions.delete_question,
                permissions.change_question,
                permissions.view_question,
                permissions.view_subsidiary,
                permissions.view_userattendance,
            ],
        )
        self.local_organizer_group.save()
