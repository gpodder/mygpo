from itertools import chain, islice

from mygpo.core.models import Podcast
from mygpo.core.proxy import proxy_object
from mygpo.db.couchdb.episode import episodes_for_podcast
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

        links = [(p.latest_episode_timestamp, lazy_call(episodes_for_podcast,
                    p, since=1, until=max_date, descending=True,
                    limit=max_per_podcast) ) for p in podcasts]

        episodes = sorted_chain(links, lambda e: e.released, reverse=True)

        for episode in islice(episodes, num_episodes):
            p = podcast_dict.get(episode.podcast, None)
            yield proxy_object(episode, podcast=p)


def lazy_call(f, *args, **kwargs):
    for x in f(*args, **kwargs):
        yield x
