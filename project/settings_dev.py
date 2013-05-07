from settings import *

DATABASES = {
        'default': {
                'ENGINE': 'django.db.backends.mysql',
                'NAME': 'dpnk',
                'USER': 'dpnk',
                'PASSWORD': 'dpnk',
                'HOST': 'localhost',
                'PORT': '',
                'OPTIONS': { 'init_command': 'SET storage_engine=INNODB,character_set_connection=utf8,collation_connection=utf8_unicode_ci, SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED' }
        },
}

SMART_SELECTS_URL_PREFIX = "http://localhost:8000"  #XXX
SITE_URL = 'http://localhost/~petr/dpnk-wp/'
DJANGO_URL = 'http://localhost:8000'
TESTING_URLS = True

LOGOUT_NEXT_PAGE = '/dpnk/profil/'
