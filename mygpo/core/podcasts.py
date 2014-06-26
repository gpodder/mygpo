from itertools import chain, islice

from mygpo.podcasts.models import Podcast, PodcastGroup
from mygpo.core.proxy import proxy_object
from mygpo.utils import sorted_chain


# the default sort order for podcasts
PODCAST_SORT=lambda p: p.display_title


class PodcastSet(set):
    """ Represents a set of podcasts """

    def __init__(self, podcasts=None):
        self.podcasts = podcasts or []


    def get_newest_episodes(self, max_date, num_episodes, max_per_podcast=5):
        """ Returns the newest episodes for a set of podcasts """

        podcast_key = lambda p: p.latest_episode_timestamp

        podcasts = filter(lambda p: p.latest_episode_timestamp, self.podcasts)
        podcasts = sorted(podcasts, key=podcast_key, reverse=True)

        # we need at most num_episodes podcasts
        podcasts = podcasts[:num_episodes]

        podcast_dict = dict((p.get_id(), p) for p in podcasts)

        # TODO: max_per_podcast
        episodes = Episode.objects.filter(podcast__in=podcasts,
                                          released__isnull=False,
                                          released__lt=max_date,
                                         )

        for episode in islice(episodes, num_episodes):
            p = podcast_dict.get(episode.podcast, None)
            yield proxy_object(episode, podcast=p)


def lazy_call(f, *args, **kwargs):
    for x in f(*args, **kwargs):
        yield x


def individual_podcasts(pg):
    """ returns individual podcasts for an iter of Podcast(Group) objects """

    for p in pg:
        if isinstance(p, Podcast):
            yield p

        elif isinstance(p, PodcastGroup):
            for x in p.podcast_set.all():
                yield x
