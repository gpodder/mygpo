from django.core.management.base import BaseCommand

from mygpo.utils import progress, multi_request_view
from mygpo.core.models import Podcast, PodcastSubscriberData
from mygpo.decorators import repeat_on_conflict


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

        total = Podcast.view('core/podcasts_by_id', limit=0).total_rows
        podcasts = multi_request_view(Podcast, 'core/podcasts_by_id')

        for n, podcast in enumerate(podcasts):

            psubscriber = PodcastSubscriberData.for_podcast(podcast.get_id())

            self.update_subscriber_data(podcast, data=psubscriber)
            self.update_podcast(podcast=podcast)

            progress(n+1, total)


    @repeat_on_conflict(['data'])
    def update_subscriber_data(self, podcast, data):
        data.subscribers = sorted(list(set(data.subscribers + podcast.subscribers)), key=lambda x: x.timestamp)
        data.save()

    @repeat_on_conflict(['podcast'], reload_f=lambda p: Podcast.for_id(p.get_id()))
    def update_podcast(self, podcast):
        podcast.subscribers = podcast.subscribers[-2:]
        podcast.save()
