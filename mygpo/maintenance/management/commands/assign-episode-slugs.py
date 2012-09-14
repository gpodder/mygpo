from datetime import datetime
from optparse import make_option

from django.core.management.base import BaseCommand

from couchdbkit.exceptions import ResourceNotFound
from couchdbkit import Consumer

from mygpo.core.models import Podcast, PodcastGroup, Episode
from mygpo.core.slugs import EpisodeSlug, EpisodesMissingSlugs
from mygpo.decorators import repeat_on_conflict
from mygpo.utils import progress
from mygpo.couch import get_main_database
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

        db = get_main_database()
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

        has_slug = lambda x: bool(x.slug)

        for seq, obj in objects:
            total = db.info()['update_seq']

            if isinstance(obj, PodcastGroup):
                podcasts = filter(has_slug, obj.podcasts)

            if isinstance(obj, Podcast):
                podcasts = filter(has_slug, [obj])

            elif isinstance(obj, Episode):
                if has_slug(obj):
                    continue

                podcast = Podcast.get(obj.podcast)
                if not podcast:
                    continue
                podcasts = filter(has_slug, [podcast])

            updated = self.handle_podcasts(podcasts)
            actions['updated'] += updated

            if not options['silent']:
                status_str = ', '.join('%s: %d' % x for x in actions.items())
                progress(seq, total, status_str)


        # finish command run status
        run_status.timestamp_finished = datetime.utcnow()
        run_status.end_seq = total
        run_status.status_counter = dict(actions)
        # and overwrite existing one (we could keep a longer log here)
        status.runs = [run_status]
        status.save()



    def handle_podcasts(self, podcasts):

        updated = 0
        for podcast in podcasts:
            common_title = podcast.get_common_episode_title()
            episodes = EpisodesMissingSlugs(podcast.get_id())

            for episode in episodes:
                slug = EpisodeSlug(episode, common_title).get_slug()
                if slug:
                    updated += 1
                    self.update_obj(obj=episode, slug=slug)

        return updated


    @repeat_on_conflict(['obj'])
    def update_obj(self, obj, slug):
        obj.set_slug(slug)
        obj.save()


    @staticmethod
    def get_objects(db, since=0, limit=1, timeout=1000):
        consumer = Consumer(db)

        while True:
            resp = consumer.wait_once(since=since, limit=limit, timeout=timeout,
                   include_docs=True, filter='slugs/slug_objects')
            results = resp['results']

            if not results:
                break

            for res in results:
                cls = (PodcastGroup, Podcast, Episode)
                classes = dict( (c._doc_type, c) for c in cls)

                doc = res['doc']
                doc_type = doc['doc_type']
                seq = res['seq']
                c = classes[doc_type]
                yield seq, c.wrap(doc)

            since = resp['last_seq']


    @staticmethod
    def get_cmd_status():
        try:
            status = CommandStatus.get('episode-slug-status')
        except ResourceNotFound:
            status = CommandStatus()
            status.command = 'Episode-Slug-Update'
            status._id = 'episode-slug-status'

        return status


    @staticmethod
    def get_since(status, options):
        if options['continue']:
            return status.last_seq
        else:
            return options['since']
