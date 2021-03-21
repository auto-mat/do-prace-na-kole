import datetime

from django.test import Client, RequestFactory, TestCase

from dpnk.test.util import print_response  # noqa
from dpnk.views_results import CompetitionResultListJson

from model_mommy import mommy


