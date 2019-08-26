from model_mommy import mommy


class Questions:
    def __init__(self, competitions, choice_types, **kwargs):
        self.team_question = mommy.make(  # was pk=6
            "dpnk.question",
            question_type = "text",
            comment_type = None,
            with_attachment = False,
            text = "Team question text",
            name = "Team question",
            required = False,
            competition = competitions.team_questionnaire,
        )

        self.basic5 = mommy.make(  # was pk=5
            "dpnk.question",
            question_type = "text",
            comment_type = None,
            with_attachment = False,
            text = "Question text",
            name = "Question 5 name",
            required = False,
            competition = competitions.questionnaire,
        )

        self.basic4 = mommy.make(  # was pk=4
            "dpnk.question",
            question_type = "text",
            comment_type = "link",
            with_attachment = True,
            name = "Question 4 name",
            competition = competitions.questionnaire,
        )

        self.with_attachment = mommy.make(  # was pk=3
            "dpnk.question",
            question_type = "text",
            comment_type = "one-liner",
            with_attachment = True,
            competition = competitions.questionnaire,
        )

        self.with_choices = mommy.make(  # was pk=1
            "dpnk.question",
            question_type = "choice",
            required = False,
            with_attachment = False,
            competition = competitions.questionnaire,
        )

        self.with_choices_and_attachment = mommy.make(  # was pk=2
            "dpnk.question",
            question_type = "choice",
            choice_type = choice_types.yes_no,
            with_attachment = True,
            competition = competitions.questionnaire,
        )
