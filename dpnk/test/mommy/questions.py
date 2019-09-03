from model_mommy import mommy


class UserAttendances:
    def __init__(self, user_attendances, **kwargs):
        self.team_question = mommy.make(  # was pk=6
            "dpnk.question",
            question_type = "text",
            comment_type = None,
            with_attachment = False,
            text = "Team question text",
            name = "Team question",
            required = False,
            competition = 13,
        )

        self.question5 = mommy.make(  # was pk=5
            "dpnk.question",
            question_type = "text",
            comment_type = None,
            with_attachment = False,
            text = "Question text",
            name = "Question 5 name",
            required = False,
            competition = 4,
        )

        self.question4 = mommy.make(  # was pk=4
            "dpnk.question",
            question_type = "text",
            comment_type = "link",
            with_attachment = True,
            name = "Question 4 name",
            competition = 4,
        )

        self.question_with_attachment = mommy.make(  # was pk=3
            "dpnk.question",
            question_type = "text",
            comment_type = "one-liner",
            with_attachment = True,
            competition = 4,
        )

        self.question_with_choices = mommy.make(  # was pk=1
            "dpnk.question",
            question_type = "choice",
            required = False,
            with_attachment = False,
            competition = 4,
        )

        self.question_with_choice_and_attachment = mommy.make(  # was pk=2
            "dpnk.question",
            question_type = "choice",
            choice_type = 1,
            with_attachment = True,
            competition = 4,
        )
