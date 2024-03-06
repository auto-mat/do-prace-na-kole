#!/usr/bin/env python

import sys

from django.core.management import BaseCommand

from dpnk.tasks import check_celerybeat_liveness


class Command(BaseCommand):
    help = "Check Celery beat liveness"  # noqa

    def handle(self, *args, **options):
        if not check_celerybeat_liveness(set_key=False):
            sys.exit(1)
