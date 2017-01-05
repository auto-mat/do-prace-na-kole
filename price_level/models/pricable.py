import datetime

from django.conf import settings
from django.db import models


class Pricable(models.Model):
    def get_current_price_level(self, date_time=datetime.datetime.now(), category=settings.PRICE_LEVELS_CATEGORY_DEFAULT):
        return self.pricelevel_set.filter(
            takes_effect_on__lte=date_time,
            category=category,
        ).order_by('-takes_effect_on').first()

    class Meta:
        abstract = True
