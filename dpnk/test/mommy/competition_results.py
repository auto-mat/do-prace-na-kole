from model_mommy import mommy


class CompetitionResults:
    def __init__(self, competitions, teams, **kwargs):
        self.basic = mommy.make(  # was pk=0
            "dpnk.competitionresult",
            team=teams.basic,
            result=100,
            competition=competitions.team_frequency_c2010,
        )
