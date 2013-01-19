from __future__ import print_function

import sys
import os.path

from django.conf import settings
from django.core.management.base import BaseCommand
from restkit import BasicAuth

from couchdbkit import Database
from couchdbkit.ext.django import *
from couchdbkit.loaders import FileSystemDocsLoader

from mygpo.users.models import User
from mygpo.decorators import repeat_on_conflict
from mygpo.db.couchdb.episode_state import episode_states_for_user
from mygpo.db.couchdb.podcast_state import podcast_states_for_user
from mygpo.db.couchdb.user import suggestions_for_user

try:
    from collections import Counter
except ImportError:
    from mygpo.counter import Counter


class Command(BaseCommand):
    """ Moves a user into its own database """

    def handle(self, *args, **options):

        if not args:
            print('Usage: ./manage.py <username> [<database url>]',
                    file=sys.stderr)
            return

        username = args[0]
        user = User.get_user(username, is_active=None)

        if not user:
            raise Exception('User does not exist')

        if len(args) > 1:
            db_url = args[1]
        else:
            base_db = settings.COUCHDB_DATABASES[0][1]
            db_url = '{base}_users%2F{username}'.format(base=base_db, username=user.username)

        print('Migrating user', user, 'to', db_url)

        db = Database(db_url, create=True)

        self.setup_ddocs(db)

        podcast_states = podcast_states_for_user(user)
        for state in podcast_states:
            self.resave_doc(db, state)

        episode_states = episode_states_for_user(user)
        for state in episode_states:
            self.resave_doc(db, state)

        suggestions = suggestions_for_user(user)
        if suggestions:
            self.resave_doc(db, suggestions)


    def resave_doc(self, db, obj):
        cls = obj.__class__
        doc = obj.to_json()
        del doc['_rev']
        obj = cls.wrap(doc)
        db[obj._id] = obj


    def setup_ddocs(self, db):
        path = os.path.join(settings.BASE_DIR, '..', 'couchdb', 'user', '_design',)
        loader = FileSystemDocsLoader(path)
        loader.sync(db, verbose=True)


    def get_filters(self):
        filters = []

        couchdb_admins = getattr(settings, 'COUCHDB_ADMINS', ())
        if couchdb_admins:
            username, passwd = couchdb_admins[0]
            filters.append(BasicAuth(username, passwd))

        return filters
