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

if os.getenv("USE_BJOERN_WSGI_SERVER") == "True":
    sys.path.append("/usr/local/src/bjoern/")
    sys.path.append("/usr/local/src/bjoern/build/")

    import signal

    import bjoern

    bjoern.listen(
        wsgi_app=application,
        host="0.0.0.0",
        port=8000,
        reuse_port=True,
    )

    worker_pids = []
    num_workers = int(os.getenv("BJOERN_WSGI_SERVER_NUM_WORKERS", 4))
    for _ in range(num_workers):
        pid = os.fork()
        if pid > 0:
            # in master
            worker_pids.append(pid)
        elif pid == 0:
            # in worker
            try:
                bjoern.run(
                    statsd={
                        "enable": True,
                        "host": os.getenv("STATSD_SERVER_HOST", "statsd"),
                        "port": int(os.getenv("STATSD_SERVER_PORT", 8125)),
                        "ns": os.getenv("STATSD_SERVER_NAME_SPACE", "bjoern"),
                    },
                )
            except KeyboardInterrupt:
                pass
            exit()

    try:
        for _ in range(num_workers):
            os.wait()
    except KeyboardInterrupt:
        for pid in worker_pids:
            os.kill(pid, signal.SIGINT)
