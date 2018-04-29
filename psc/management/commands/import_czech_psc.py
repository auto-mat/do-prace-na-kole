#!/usr/bin/python3
import csv
import io

from django.core.management.base import BaseCommand

from psc.models import PSC

import requests


class Command(BaseCommand):
    help = 'Import Czech PSČ (zipcode) table into the database' # noqa

    def handle(self, *args, **kwargs):
        psc_table = requests.get("https://raw.githubusercontent.com/sedrickcz/psc-cr/master/psc.csv").content
        dictReader = csv.DictReader(
            io.StringIO(psc_table.decode('utf-8')),
            delimiter=',',
        )

        for row in dictReader:
            PSC.objects.create(
                municipality_name=row['district'],
                municipality_part_name=row['name'],
                psc=int(row['zipcode']),
                code=int(row['zipcode']),
            )
