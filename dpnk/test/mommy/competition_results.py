from model_mommy import mommy


class CompetitionResults:
    def __init__(self, competitions, teams, **kwargs):
        self.basic = mommy.make(  # was pk=0
            "dpnk.competitionresult",
            team = 1,
            result = 100,
            competition = 3,
        )
