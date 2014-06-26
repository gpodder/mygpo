
""" Create the Elasticsearch index """

import sys

from django.core.management.base import BaseCommand

from mygpo.search.index import create_index


class Command(BaseCommand):

    help = sys.modules[__name__].__doc__

    def handle(self, *args, **options):
        create_index()
