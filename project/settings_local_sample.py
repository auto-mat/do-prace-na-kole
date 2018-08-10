# -*- coding: utf-8 -*-
import os

from .settings_dev import *  # noqa

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.environ.get('DPNK_DB_NAME', 'dpnk'),
        'USER': os.environ.get('DPNK_DB_USER', 'dpnk'),
        'PASSWORD': os.environ.get('DPNK_DB_PASSWORD', ''),
        'HOST': os.environ.get('DPNK_DB_HOST', 'localhost'),
        'PORT': os.environ.get('DPNK_DB_PORT', ''),
        'CONN_MAX_AGE': 0,
    },
}
SECRET_KEY = 'CHANGE_ME'
