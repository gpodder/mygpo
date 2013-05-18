from django.core.management.base import BaseCommand
from mygpo.db.couchdb.utils import sync_design_docs


class Command(BaseCommand):
    """ Sync design docs from filesystem """

    def handle(self, *args, **options):

        sync_design_docs()
