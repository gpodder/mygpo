from datetime import datetime
from collections import defaultdict


DEFAULT_RELEASE = datetime(1970, 1, 1)
_SORT_KEY = lambda eps: eps[0].released or DEFAULT_RELEASE

class PodcastGrouper(object):
    """ Groups episodes of two podcasts based on certain features

    The results are sorted by release timestamp """

    DEFAULT_RELEASE = datetime(1970, 1, 1)

    def __init__(self, podcast1, podcast2):

        if None in (podcast1, podcast2):
            raise ValueError('podcasts must not be None')

        self.podcast1 = podcast1
        self.podcast2 = podcast2


    def __get_episodes(self):
        episodes = dict((e._id, e) for e in self.podcast1.get_episodes())
        episodes2 = dict((e._id, e) for e in self.podcast2.get_episodes())
        episodes.update(episodes2)
        return episodes


    def group(self, get_features):

        episodes = self.__get_episodes()

        episode_groups = defaultdict(list)

        episode_features = map(get_features, episodes.items())

        for features, episode_id in episode_features:
            episode = episodes[episode_id]
            episode_groups[features].append(episode)

        groups = sorted(episode_groups.values(), key=_SORT_KEY)

        return enumerate(groups)
