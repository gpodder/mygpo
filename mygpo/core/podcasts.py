from itertools import chain, islice

import gevent

from mygpo.core.models import Podcast
from mygpo.core.proxy import proxy_object


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

        jobs = [gevent.spawn(Podcast.get_episodes, podcast, since=1,
                until=max_date, descending=True,
                limit=max_per_podcast) for podcast in podcasts]

        gevent.joinall(jobs)

        episodes = chain.from_iterable(job.get() for job in jobs)

        episodes = sorted(episodes, key=lambda e: e.released, reverse=True)

        for episode in islice(episodes, num_episodes):
            p = podcast_dict.get(episode.podcast, None)
            yield proxy_object(episode, podcast=p)
