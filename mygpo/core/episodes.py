from itertools import chain, islice

import gevent

from mygpo.core.models import Podcast
from mygpo.core.proxy import proxy_object


class NewestEpisodes(object):
    """ Returns the newest episodes for a set of podcasts """

    def __init__(self, podcasts, max_date, num_episodes, max_per_podcast=5):
        self.podcasts = podcasts
        self.max_date = max_date
        self.num_episodes = num_episodes
        self.max_per_podcast = max_per_podcast


    def __iter__(self):
        podcast_key = lambda p: p.latest_episode_timestamp

        podcasts = filter(lambda p: p.latest_episode_timestamp, self.podcasts)
        podcasts = sorted(podcasts, key=podcast_key, reverse=True)

        # we need at most num_episodes podcasts
        podcasts = podcasts[:self.num_episodes]

        podcast_dict = dict((p.get_id(), p) for p in podcasts)

        jobs = [gevent.spawn(Podcast.get_episodes, podcast, since=1,
                until=self.max_date, descending=True,
                limit=self.max_per_podcast) for podcast in podcasts]

        gevent.joinall(jobs)

        episodes = chain.from_iterable(job.get() for job in jobs)

        episodes = sorted(episodes, key=lambda e: e.released, reverse=True)

        for episode in islice(episodes, self.num_episodes):
            p = podcast_dict.get(episode.podcast, None)
            yield proxy_object(episode, podcast=p)
