import sys
from datetime import datetime
from time import sleep
from urlparse import urlparse
from optparse import make_option

from couchdbkit import Database
from restkit import BasicAuth
from django.core.management.base import BaseCommand
from django.conf import settings

from mygpo.decorators import repeat_on_conflict
from mygpo.utils import progress



class Command(BaseCommand):
    """ Queries a view in each design document to keep the view-files hot """

    option_list = BaseCommand.option_list + (
        make_option('--exclude', action='append', dest='exclude', default=[],
            help='Exclude views that contain the text as substring'),
    )


    def handle(self, *args, **options):
        db_urls = set(db['URL'] for db in settings.COUCHDB_DATABASES.values())

        filters = []

        exclude = options['exclude']

        couchdb_admins = getattr(settings, 'COUCHDB_ADMINS', ())
        if couchdb_admins:
            username, passwd = couchdb_admins[0]
            filters.append(BasicAuth(username, passwd))

        for db_url in db_urls:
            db = Database(db_url, filters=filters)

            for sig, ddoc_name in self.get_design_docs(db, exclude):
                ddoc = db['_design/' + ddoc_name]
                if not ddoc.get('views', {}):
                    continue

                view_name = ddoc['views'].keys()[0]
                print 'touching %s %s %s/%s' % (db_url, sig[:5], ddoc_name, view_name),
                self.touch_view(db, ddoc_name, view_name)
                print



    @staticmethod
    def get_all_design_docs(db):
        """ Returns all design documents in the database """

        prefix = '_design/'
        prefix_len = len(prefix)
        return (ddoc['key'][prefix_len:] for ddoc in db.view('_all_docs', startkey='_design/', endkey='_design0'))


    def get_design_docs(self, db, exclude=[]):
        """
        Return one design doc for each index file
        """
        ddocs = {}
        for ddoc in self.get_all_design_docs(db):
            if any(e in ddoc for e in exclude):
                continue

            sig = db.res.get('/_design/%s/_info' % ddoc).json_body['view_index']['signature']
            ddocs[sig] = ddoc

        return ddocs.items()


    def touch_view(self, db, ddoc, view):
        r = list(db.view('%s/%s' % (ddoc, view), limit=0, stale='update_after'))
