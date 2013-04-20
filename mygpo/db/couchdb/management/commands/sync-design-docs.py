import os.path

from django.conf import settings
from django.core.management.base import BaseCommand

from couchdbkit import Database
from couchdbkit.loaders import FileSystemDocsLoader
from couchdbkit.ext.django import loading
from restkit import BasicAuth

from mygpo.db.couchdb import get_main_database



class Command(BaseCommand):
    """ Sync design docs from filesystem """

    def handle(self, *args, **options):

        for part, label in settings.COUCHDB_DDOC_MAPPING.items():
            path = os.path.join(settings.BASE_DIR, '..', 'couchdb', part, '_design')
            db = loading.get_db(label)
            loader = FileSystemDocsLoader(path)
            loader.sync(db, verbose=True)
