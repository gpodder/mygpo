from datetime import datetime
from collections import defaultdict


DEFAULT_RELEASE = datetime(1970, 1, 1)
_SORT_KEY = lambda eps: eps[0].released or DEFAULT_RELEASE


class PodcastGrouper(object):
    """Groups episodes of two podcasts based on certain features

    The results are sorted by release timestamp"""

    DEFAULT_RELEASE = datetime(1970, 1, 1)

    def __init__(self, podcasts):

        if not podcasts or (None in podcasts):
            raise ValueError("podcasts must not be None")

        self.podcasts = podcasts

    def __get_episodes(self):
        episodes = {}
        for podcast in self.podcasts:
            episodes.update(dict((e.id, e.id) for e in podcast.episode_set.all()))

        return episodes

    def group(self, get_features):

        episodes = self.__get_episodes()

        episode_groups = defaultdict(list)

        episode_features = map(get_features, episodes.items())

        for features, episode_id in episode_features:
            episode = episodes[episode_id]
            episode_groups[features].append(episode)

        # groups = sorted(episode_groups.values(), key=_SORT_KEY)
        groups = episode_groups.values()

        return enumerate(groups)
