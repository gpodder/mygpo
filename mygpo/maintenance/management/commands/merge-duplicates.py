from django.core.management.base import BaseCommand

from mygpo.maintenance import merge

class Command(BaseCommand):


    def handle(self, *args, **options):

        merge.merge_objects()

