from model_mommy import mommy


class ChoiceTypes:
    def __init__(self, competitions, **kwargs):
        self.yes_no = mommy.make(  # was pk=1
            "dpnk.choicetype",
            name = "yes/no",
            competition = competitions.questionnaire,
        )
