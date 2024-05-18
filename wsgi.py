"""
WSGI config for newprj project.

This module contains the WSGI application used by Django's development server
and any production WSGI deployments. It should expose a module-level variable
named ``application``. Django's ``runserver`` and ``runfcgi`` commands discover
this application via the ``WSGI_APPLICATION`` setting.

Usually you will have the standard Django WSGI application here, but it also
might make sense to replace the whole Django WSGI application with a custom one
that later delegates to the Django one. For example, you could introduce WSGI
middleware here, or combine a Django application with an application of another
framework.

"""
import os
import site
import sys

from django.core.wsgi import get_wsgi_application

import newrelic.agent

from project.settings import PROJECT_ROOT


newrelic.agent.initialize(os.path.join(PROJECT_ROOT, "newrelic.ini"))

# ALLDIRS = [
#     os.path.join(PROJECT_ROOT, "env/lib/python2.6/site-packages"),
# ]

# # Remember original sys.path.
# prev_sys_path = list(sys.path)

# # Add each new site-packages directory.
# for directory in ALLDIRS:
#     site.addsitedir(directory)

# # Reorder sys.path so new directories at the front.
# new_sys_path = []
# for item in list(sys.path):
#     if item not in prev_sys_path:
#         new_sys_path.append(item)
#         sys.path.remove(item)
# sys.path[:0] = new_sys_path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

# This application object is used by any WSGI server configured to use this
# file. This includes Django's development server, if the WSGI_APPLICATION
# setting points here.
application = get_wsgi_application()
application = newrelic.agent.wsgi_application()(application)

# Apply WSGI middleware here.
# from helloworld.wsgi import HelloWorldApplication
# application = HelloWorldApplication(application)

if os.getenv("USE_BJOERN_WSGI_SERVER") == "true":
    sys.path.append("/usr/local/src/bjoern/")

    import bjoern

    bjoern.run(
        wsgi_app=application,
        host="0.0.0.0",
        port=8000,
        statsd={
            "enable": True,
            "host": "${STATSD_SERVER_HOST:-'statsd'}",
            "port": "${STATSD_SERVER_PORT:-'8125'}",
            "ns": "${STATSD_SERVER_NAME_SPACE:-'bjoern'}",
        },
    )
