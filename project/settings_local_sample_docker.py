# -*- coding: utf-8 -*-
from .settings_dev import *  # noqa

SECRET_KEY = 'CHANGE_ME'

SITE_URL = 'localhost:8000'
DJANGO_URL = 'http://localhost:8000'

ACCESS_CONTROL_ALLOW_ORIGIN = ("http://localhost", )

BROKER_URL = 'amqp://guest@rabbit/'
