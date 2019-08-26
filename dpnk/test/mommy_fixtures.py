from .cities import Cities
from .companies import Companies
from .commute_modes import CommuteModes


target_dag = [
    ("cities", Cities, set()),
    ("commute_modes", CommuteModes, set()),
    ("groups", Groups, set()),
    ("users", Users, {"groups", "cities", "companies"}),
    ("companies", Companies, {"commute_modes"}),
    ("teams", Teams, {"campaigns", "subsidiaries"}),
    ("tshirt_sizes", TShirtSizes, {"campaigns"}),
    ("user_attendances", UserAttendances, {"users", "campaigns"}),
]

class Fixtures():
    """
    Sets up a set of testing objects which are used throughout the test suit.

    Assumes that the commute_mode.json fixture is loaded.
    """
    def __init__(self, targets):
        self.sets = {}
        while targets:
            if target_dag[targets[0]][2].issubset(set(sets.keys())):
                target = target_dag[targets.pop(0)]
                self.sets[target[0]] = target[1](kwargs=self.sets)
