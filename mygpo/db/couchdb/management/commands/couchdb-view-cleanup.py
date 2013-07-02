from django.core.management.base import BaseCommand
from mygpo.db.couchdb.utils import view_cleanup


class Command(BaseCommand):
    """ Sync design docs from filesystem """

    def handle(self, *args, **options):

        view_cleanup()
