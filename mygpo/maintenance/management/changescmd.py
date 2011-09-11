from datetime import datetime
from optparse import make_option
from abc import abstractmethod

from django.core.management.base import BaseCommand

from couchdbkit.exceptions import ResourceNotFound

from mygpo.utils import progress
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


    def handle(self, *args, **options):

        db = self.get_db()

        status = self.get_cmd_status()
        since = self.get_since(status, options)
        objects = self.get_objects(db, since)
        actions = Counter()


        # create unfinished command run status
        run_status = CommandRunStatus()
        run_status.timestamp_started = datetime.utcnow()
        run_status.start_seq = since
        # add it to existing one (if any)
        status.runs.append(run_status)
        status.save()

        total = db.info()['update_seq']
        status_str = ''

        for seq, obj in objects:
            total = db.info()['update_seq']

            self.handle_obj(seq, obj, actions)

            if not options['silent']:
                status_str = ', '.join('%s: %d' % x for x in actions.items())
                progress(seq, total, status_str)

        progress(total, total, status_str)

        # finish command run status
        run_status.timestamp_finished = datetime.utcnow()
        run_status.end_seq = total
        run_status.status_counter = dict(actions)
        # and overwrite existing one (we could keep a longer log here)
        status.runs = [run_status]
        status.save()


    @abstractmethod
    def handle_obj(seq, obj, actions):
        raise NotImplemented


    @abstractmethod
    def get_objects(self, db, since=0, limit=1):
        raise NotImplemented


    def get_cmd_status(self):
        status_id = self.get_status_id()
        try:
            status = CommandStatus.get(status_id)
        except ResourceNotFound:
            status = CommandStatus()
            status.command = self.get_command_name()
            status._id = status_id

        return status


    @staticmethod
    def get_since(status, options):
        if options['continue']:
            return status.last_seq
        else:
            return options['since']


    @abstractmethod
    def get_db(self):
        raise NotImplemented


    @abstractmethod
    def get_status_id(self):
        raise NotImplemented

    @abstractmethod
    def get_command_name(self):
        raise NotImplemented
