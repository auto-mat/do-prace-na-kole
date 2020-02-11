from dpnk import models


class CommuteModes:
    def __init__(self, **kwargs):
        self.bicycle = models.CommuteMode.objects.get(pk=1)
        self.by_foot = models.CommuteMode.objects.get(pk=2)
        self.by_other_vehicle = models.CommuteMode.objects.get(pk=3)
        self.no_work = models.CommuteMode.objects.get(pk=4)
