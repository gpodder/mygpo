from math import floor

from django.core.management.base import BaseCommand

from mygpo.directory.toplist import PodcastToplist
from mygpo.users.models import EpisodeUserState
from mygpo.utils import progress
from mygpo.core.models import Podcast, PodcastGroup
from mygpo.decorators import repeat_on_conflict
from mygpo.maintenance.management.podcastcmd import PodcastCommand
from mygpo.db.couchdb.episode_state import all_podcast_episode_states


class Command(PodcastCommand):
    """ Calculates the times between an episode is published, first downloaded
    and played (per user).

    The times are reported in quantiles of the accumulated values for each
    podcast. The output contains two lines for each podcast, both starting with
    the podcast's URL. One for the interval episode published - downloads, one
    for downloads - plays.
    """

    def handle(self, *args, **options):

        podcasts = self.get_podcasts(*args, **options)

        for n, podcast in enumerate(podcasts):
            i1, i2 = self.get_listener_stats(podcast)

            if i1 or i2:
                print podcast.url, ' '.join(str(q) for q in quantiles(i1, 100))
                print podcast.url, ' '.join(str(q) for q in quantiles(i2, 100))


    def get_listener_stats(self, podcast):

        # times in seconds between episodes being published,
        # and first listen events
        i1 = []

        # times in seconds between first download and first listen events
        i2 = []

        episodes = {e.id: e for e in podcast.episode_set.all()}

        for state in all_podcast_episode_states(podcast):
            ep = episodes.get(state.episode, None)

            dl = self.first_action(state.actions, 'download')

            if dl and None not in (ep, dl.timestamp):
                i1.append(total_seconds(dl.timestamp - ep))

            pl = self.first_action(state.actions, 'play')

            if None not in (dl, pl) and \
               None not in (dl.timestamp, pl.timestamp):
                i2.append(total_seconds(pl.timestamp - dl.timestamp))

        return i1, i2


    @staticmethod
    def first_action(actions, action_type):
        for a in actions:
            if a.action == action_type:
                return a


def quantiles(data, intervals=100):
    """
    http://en.wikipedia.org/wiki/Quantile

    Divide DATA in INTERVALS intervals and return the boundaries of
    the intervals.  A median has two intervals.  Thus, three values
    will be returned: the botton of the lower half, the point that
    divides the lower and upper half and the top of the upper half.

    Taking the median of [1, 2, 3, 4, 5] returns [1, 3, 5].

       |   |   |
       1 2 3 4 5
    """

    data = sorted(data)

    q = list()

    if not data:
        return q

    q.append(data[0])
    for i in xrange(intervals - 1):
        i += 1
        q.append(data[int(floor(float(i * len(data)) / intervals))])
    q.append(data[-1])

    return q


def total_seconds(td):
    """ Returns the total amount of seconds of the timedelta

    timedelta.total_seconds() is new in Python 2.7
    http://docs.python.org/library/datetime.html#datetime.timedelta.total_seconds """
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6
