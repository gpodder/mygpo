from datetime import datetime
from optparse import make_option
from abc import abstractmethod

from django.core.management.base import BaseCommand

from couchdbkit.exceptions import ResourceNotFound
from couchdbkit import Consumer

from mygpo.utils import progress
from mygpo.couch import get_main_database
from mygpo.maintenance.models import CommandStatus, CommandRunStatus

try:
    from collections import Counter
except ImportError:
    from mygpo.counter import Counter



class ChangesCommand(BaseCommand):
    """ base class for commands that operate on the CouchDB _changes feed """

    option_list = BaseCommand.option_list + (
        make_option('--since', action='store', type=int, dest='since',
            default=0, help="Where to start the operation"),

        make_option('--continue', action='store_true', dest='continue',
            default=False, help="Continue from last sequence number"),

        make_option('--silent', action='store_true', dest='silent',
            default=False, help="Don't display any progress output"),
    )


    def __init__(self, status_id, command_name):
        self.status_id = status_id
        self.command_name = command_name


    def handle(self, *args, **options):

        self.db = self.get_db()

        status = self.get_cmd_status()
        since = self.get_since(status, options)
        self.actions = Counter()


        # create unfinished command run status
        run_status = CommandRunStatus()
        run_status.timestamp_started = datetime.utcnow()
        run_status.start_seq = since
        # add it to existing one (if any)
        status.runs.append(run_status)
        status.save()

        if options['silent']:
            # "disable" print_status
            self.print_status = lambda *args, **kwargs: None

        try:
            self.process(self.db, since)

        finally:
            # finish command run status
            total = self.db.info()['update_seq']
            run_status.timestamp_finished = datetime.utcnow()
            run_status.end_seq = total
            run_status.status_counter = dict(self.actions)
            # and overwrite existing one (we could keep a longer log here)
            status.runs = [run_status]
            status.save()


    def callback(self, line):
        seq = line['seq']
        doc = line['doc']

        self.handle_obj(seq, doc, self.actions)
        self.print_status(seq, self.actions)


    def print_status(self, seq, actions):
        counter = getattr(self, 'counter', 0)
        if counter % 1000 == 0:
            self.total = self.db.info()['update_seq']
        self.counter = counter + 1

        status_str = ', '.join('%s: %d' % x for x in self.actions.items())
        progress(seq, self.total, status_str)


    @abstractmethod
    def handle_obj(seq, obj, actions):
        raise NotImplemented


    @abstractmethod
    def process(self, db, since):
        consumer = Consumer(db)
        params = self.get_query_params()
        consumer.wait(self.callback, since=since, heartbeat=10000, **params)


    def get_cmd_status(self):
        try:
            status = CommandStatus.get(self.status_id)
        except ResourceNotFound:
            status = CommandStatus()
            status.command = self.command_name
            status._id = self.status_id

        return status


    def get_query_params(self):
        return dict(include_docs=True)


    @staticmethod
    def get_since(status, options):
        if options['continue']:
            return status.last_seq
        else:
            return options['since']


    @abstractmethod
    def get_db(self):
        return get_main_database()
