import sys
from datetime import datetime
from time import sleep

from couchdbkit import Database
from django.core.management.base import BaseCommand
from django.conf import settings

from mygpo.decorators import repeat_on_conflict
from mygpo.core.models import SanitizingRule
from mygpo.utils import progress



class Command(BaseCommand):
    """
    Compacts the database and all views, and measures the required time
    """

    DESIGN_DOCS = ('core', 'users', 'directory', 'maintenance', 'django_couchdb_utils', )


    def handle(self, *args, **options):

        db_url = settings.COUCHDB_DATABASES[0][1]
        db = Database(db_url)

        print 'Compacting Database ... ',
        sys.stdout.flush()
        compact_db = lambda: db.compact()
        db_is_compacting = lambda: db.info()['compact_running']
        duration = self.compact_wait(compact_db, db_is_compacting)
        print duration

        for design_doc in self.DESIGN_DOCS:
            print 'Compacting %s ...' % design_doc,
            sys.stdout.flush
            compact_view = lambda: db.compact('%s' % design_doc)
            view_is_compacting = lambda: db.res.get('/_design/%s/_info' % design_doc).json_body['view_index']['compact_running']
            duration = self.compact_wait(compact_view, view_is_compacting)
            print duration


    @staticmethod
    def compact_wait(compact, is_compacting, sleep_time=1, inc_factor = 2):

        start = datetime.utcnow()
        compact()

        while is_compacting():
            sleep(sleep_time)
            sleep_time *= inc_factor

        end = datetime.utcnow()

        return end - start
