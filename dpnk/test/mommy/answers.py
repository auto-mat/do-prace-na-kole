from model_mommy import mommy


class Answers:
    def __init__(self, userattendances, questions, choices, **kwargs):
        self.answer_with_picture = mommy.make(  # was pk=1
            "dpnk.answer",
            user_attendance=userattendances.userattendance,
            question=questions.with_attachment,
            attachment="DSC00002.JPG",
            points_given=3.2,
            comment="Testing comment",
        )

        self.answer_without_attachment = mommy.make(  # was pk=5
            "dpnk.answer",
            user_attendance=userattendances.userattendance,
            choices=[choices.yes],
            comment="Answer without attachment",
            attachment=None,
            question=questions.with_choices_and_attachment,
        )

        self.answer_with_gpx = mommy.make(  # was pk=2
            "dpnk.answer",
            user_attendance=userattendances.userattendance,
            attachment="modranska-rokle.gpx",
            comment_given="Given comment",
            choices=[choices.no],
            question=questions.basic4,
        )

        self.answer_2009_ua = mommy.make(  # was pk=3
            "dpnk.answer",
            user_attendance=userattendances.userattendance2009,
            question=questions.with_choices_and_attachment,
        )

        self.answer_with_picture_and_choice = mommy.make(  # was pk=4
            "dpnk.answer",
            user_attendance=userattendances.userattendance2,
            choices=[choices.no],
            question=questions.with_choices_and_attachment,
            attachment="DSC00002.JPG",
        )
