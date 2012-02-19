from django.core.management.base import BaseCommand

from mygpo.utils import progress, multi_request_view
from mygpo.core.models import Podcast, PodcastSubscriberData
from mygpo.decorators import repeat_on_conflict
from mygpo.counter import Counter


class Command(BaseCommand):
    """
    Moves SubscriberData from a Podcast to its PodcastSubscriberData document.

    new SubscriberData is added (for example by update-toplist) to the Podcast
    so that it always has the most current data available. To avoid too big
    Podcast documents, this command moves old data to a separate document,
    leaving the latest two entries in both the Podcast and its
    PodcastSubscriberData document.
    """

    def handle(self, *args, **options):

        total = Podcast.count()
        podcasts = Podcast.all_podcasts()
        actions = Counter()

        for n, podcast in enumerate(podcasts):

            psubscriber = PodcastSubscriberData.for_podcast(podcast.get_id())

            res = self.update_subscriber_data(podcast, data=psubscriber)
            self.update_podcast(podcast=podcast)

            action = 'updated' if res else 'skipped'
            actions[action] += 1

            status_str = ', '.join('%s: %d' % x for x in actions.items())
            progress(n+1, total, status_str)


    @repeat_on_conflict(['data'])
    def update_subscriber_data(self, podcast, data):
        l1 = len(data.subscribers)

        subscribers = set(data.subscribers + podcast.subscribers)
        data.subscribers = sorted(subscribers, key=lambda x: x.timestamp)

        if len(data.subscribers) != l1:
            data.save()
            return True


    @repeat_on_conflict(['podcast'], reload_f=lambda p: Podcast.get(p.get_id()))
    def update_podcast(self, podcast):
        if len(podcast.subscribers) > 2:
            podcast.subscribers = podcast.subscribers[-2:]
            podcast.save()
