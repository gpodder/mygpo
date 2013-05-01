import os.path

from django.conf import settings
from django.core.management.base import BaseCommand
from couchdbkit.loaders import FileSystemDocsLoader
from couchdbkit.ext.django import loading


class Command(BaseCommand):
    """ Sync design docs from filesystem """

    def handle(self, *args, **options):

        base_dir = settings.BASE_DIR

        for part, label in settings.COUCHDB_DDOC_MAPPING.items():
                path = os.path.join(base_dir, '..', 'couchdb', part, '_design')
                db = loading.get_db(label)
                loader = FileSystemDocsLoader(path)
                loader.sync(db, verbose=True)
