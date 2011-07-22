from optparse import make_option
from datetime import datetime

from django.core.management.base import BaseCommand
from couchdbkit import Consumer
from couchdbkit.exceptions import ResourceNotFound

from mygpo.core.models import Episode
from mygpo.users.models import EpisodeUserState
from mygpo.utils import progress
from mygpo.decorators import repeat_on_conflict
from mygpo.maintenance.models import CommandStatus, CommandRunStatus

try:
    from collections import Counter
except ImportError:
    from mygpo.counter import Counter


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--since', action='store', type=int, dest='since',
            default=0, help="Where to start the operation"),

        make_option('--continue', action='store_true', dest='continue',
            default=False, help="Continue from last sequence number"),

        make_option('--silent', action='store_true', dest='silent',
            default=False, help="Don't display any progress output"),
    )


    def handle(self, *args, **options):
        db = EpisodeUserState.get_db()
        status = self.get_cmd_status()
        since = self.get_since(status, options)
        states = self.get_states(db, since)
        actions = Counter()

        # create unfinished command run status
        run_status = CommandRunStatus()
        run_status.timestamp_started = datetime.utcnow()
        run_status.start_seq = since
        # add it to existing one (if any)
        status.runs.append(run_status)
        status.save()

        total = db.info()['update_seq']

        for seq, state in states:
            total = db.info()['update_seq']

            try:
                episode = Episode.get(state.episode)
            except:
                episode = None

            if episode:
                listeners = episode.listener_count()
                actions['updated'] += self.update(episode=episode, listeners=listeners)
            else:
                actions['missing'] += 1

            if not options['silent']:
                progress(seq, total, ', '.join('%s: %d' % x for x in actions.items()))


        # finish command run status
        run_status.timestamp_finished = datetime.utcnow()
        run_status.end_seq = total
        run_status.status_counter = dict(actions)
        # and overwrite existing one (we could keep a longer log here)
        status.runs = [run_status]
        status.save()


    @staticmethod
    def get_cmd_status():
        try:
            status = CommandStatus.get('episode-toplist-status')
        except ResourceNotFound:
            status = CommandStatus()
            status.command = 'Episode-Toplist-Update'
            status._id = 'episode-toplist-status'

        return status


    @staticmethod
    def get_since(status, options):
        if options['continue']:
            return status.last_seq
        else:
            return options['since']



    @repeat_on_conflict(['episode'])
    def update(self, episode, listeners):
        if episode.listeners == listeners:
            return False

        episode.listeners = listeners
        episode.save()
        return True


    @staticmethod
    def get_states(db, since=0, limit=10, timeout=10):
        consumer = Consumer(db)

        while True:
            resp = consumer.wait_once(since=since, limit=limit, timeout=timeout, include_docs=True, filter='directory/has_play_events')
            results = resp['results']

            if not results:
                break

            for res in results:
                doc = res['doc']
                seq = res['seq']
                yield seq, EpisodeUserState.wrap(doc)

            since = resp['last_seq']
