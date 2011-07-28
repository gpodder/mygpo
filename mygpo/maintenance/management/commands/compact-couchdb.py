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

    def handle(self, *args, **options):
        db_url = settings.COUCHDB_DATABASES[0][1]
        db = Database(db_url)

        for name, compact, is_compacting, get_size in self.get_compacters(db):
            duration, size_before, size_after = self.compact_wait(compact, is_compacting, get_size)
            print '%-30s %17s %10s %10s' % (name, duration, self.prettySize(size_before), self.prettySize(size_after))


    def get_compacters(self, db):
        """ Returns tuples containing compaction tasks """

        compact_db       = lambda: db.compact()
        db_is_compacting = lambda: db.info()['compact_running']
        get_db_size      = lambda: db.info()['disk_size']

        yield ('database', compact_db, db_is_compacting, get_db_size)

        for design_doc in self.get_design_docs(db):
            compact_view       = lambda: db.compact('%s' % design_doc)
            view_is_compacting = lambda: db.res.get('/_design/%s/_info' % design_doc).json_body['view_index']['compact_running']
            get_view_size      = lambda: db.res.get('/_design/%s/_info' % design_doc).json_body['view_index']['disk_size']
            yield (design_doc, compact_view, view_is_compacting, get_view_size)


    @staticmethod
    def get_all_design_docs(db):
        """ Returns all design documents in the database """

        prefix = '_design/'
        prefix_len = len(prefix)
        return (ddoc['key'][prefix_len:] for ddoc in db.view('_all_docs', startkey='_design/', endkey='_design0'))


    def get_design_docs(self, db):
        """
        Return one design doc for each index file
        """
        ddocs = {}
        for ddoc in self.get_all_design_docs(db):
            sig = db.res.get('/_design/%s/_info' % ddoc).json_body['view_index']['signature']
            ddocs[sig] = ddoc

        return ddocs.values()


    @staticmethod
    def compact_wait(compact, is_compacting, get_size, sleep_time=300, inc_factor = 1):
        """ Compacts the view and waits for the compaction to finish

        Reports elapsed time and the view size, before and after the compaction """

        start = datetime.utcnow()
        size_before = get_size()

        while True:
            try:
                compact()
                break
            except Exception, e:
                sleep(100)
                print >> sys.stderr, e

        while True:
            try:
                is_comp = is_compacting()
                if is_comp:
                    sleep(sleep_time)
                    sleep_time *= inc_factor
                else:
                    break

            except Exception, e:
                sleep(100)
                print >> sys.stderr, e

        end = datetime.utcnow()
        size_after = get_size()

        return end - start, size_before, size_after


    @staticmethod
    def prettySize(size):
        # http://snippets.dzone.com/posts/show/5434
        suffixes = [("B",2**10), ("K",2**20), ("M",2**30), ("G",2**40), ("T",2**50)]
        for suf, lim in suffixes:
            if size > lim:
                continue
            else:
                return round(size/float(lim/2**10),2).__str__()+suf
