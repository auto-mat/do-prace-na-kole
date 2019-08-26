from model_mommy import mommy


class Groups:
    def __init__(self, **kwargs):
        self.cykloservis_group = mommy.make(  # was pk=5
            "auth.group",
            name = "cykloservis",
        )

        self.local_organizer_group = mommy.make(  # was pk=4
            "auth.group",
            name = "mistni koordinator",
        )
        self.local_organizer_group.permissions.set(
            [
                [
                    "view_company",
                    "dpnk",
                    "company"
                ],
                [
                    "view_companyadmin",
                    "dpnk",
                    "companyadmin"
                ],
                [
                    "add_competition",
                    "dpnk",
                    "competition"
                ],
                [
                    "delete_competition",
                    "dpnk",
                    "competition"
                ],
                [
                    "change_competition",
                    "dpnk",
                    "competition"
                ],
                [
                    "view_competition",
                    "dpnk",
                    "competition"
                ],
                [
                    "add_question",
                    "dpnk",
                    "question"
                ],
                [
                    "delete_question",
                    "dpnk",
                    "question"
                ],
                [
                    "change_question",
                    "dpnk",
                    "question"
                ],
                [
                    "view_question",
                    "dpnk",
                    "question"
                ],
                [
                    "view_subsidiary",
                    "dpnk",
                    "subsidiary"
                ],
                [
                    "view_userattendance",
                    "dpnk",
                    "userattendance"
                ]
            ]
        )
        self.local_organizer_group.save()
