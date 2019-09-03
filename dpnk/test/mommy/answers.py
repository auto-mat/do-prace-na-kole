from model_mommy import mommy


class UserAttendances:
    def __init__(self, user_attendances, **kwargs):
        self.answer_with_picture = mommy.make(  # was pk=1
            "dpnk.answer",
            user_attendance = user_attendances.userattendance,
            question = 3,
            attachment = "DSC00002.JPG",
            points_given = 3.2,
            comment = "Testing comment",
        )

        self.answer_without_attachment = mommy.make(  # was pk=5
            "dpnk.answer",
            user_attendance = user_attendances.userattendance,
            choices = [1],
            comment = "Answer without attachment",
            attachment = None,
            question = 2,
        )

        self.answer_with_gpx = mommy.make(  # was pk=2
            "dpnk.answer",
            user_attendance = user_attendances.userattendance,
            attachment = "modranska-rokle.gpx",
            comment_given = "Given comment",
            choices = [2],
            question = 4,
        )

        self.answer_2009_ua = mommy.make(  # was pk=3
            "dpnk.answer",
            user_attendance = userattendances.userattendance2009,
            question = 2,
        )

        self.answer_with_picture_and_choice = mommy.make(  # was pk=4
            "dpnk.answer",
            user_attendance = user_attendances.userattendance,
            choices = [2],
            question = 2,
            attachment = "DSC00002.JPG",
        )
