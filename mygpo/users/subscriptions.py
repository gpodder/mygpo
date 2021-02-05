from mygpo.podcasts.models import Podcast
from mygpo.history.stats import played_episode_counts


class PodcastSorter(object):
    """ Sorts a list of podcast """

    def __init__(self, podcasts):
        self.podcasts = podcasts
        self.sorted_podcasts = None

    def _sort(self):
        return self.podcasts

    def __len__(self):
        return len(self.podcasts)

    def __getitem__(self, val):
        if self.sorted_podcasts is None:
            self.sorted_podcasts = self._sort()

        return self.sorted_podcasts.__getitem__(val)

    def __iter__(self):
        if self.sorted_podcasts is None:
            self.sorted_podcasts = self._sort()

        return iter(self.sorted_podcasts)


class PodcastPercentageListenedSorter(PodcastSorter):
    """Sorts podcasts by the percentage of listened episodes

    Adds the attributes percent_listened and episodes_listened to the podcasts

    Cost: 1 DB query"""

    def __init__(self, podcasts, user):
        super(PodcastPercentageListenedSorter, self).__init__(podcasts)
        self.user = user

    def _sort(self):

        SORT_KEY = lambda podcast: podcast.percent_listened

        counts = played_episode_counts(self.user)
        for podcast in self.podcasts:
            c = counts.get(podcast.id, 0)
            if podcast.episode_count:
                podcast.percent_listened = c / float(podcast.episode_count)
                podcast.episodes_listened = c
            else:
                podcast.percent_listened = 0
                podcast.episodes_listened = 0

        return sorted(self.podcasts, key=SORT_KEY, reverse=True)


def subscription_changes(device_id, podcast_states, since, until):
    """ returns subscription changes for the device and podcast states """

    add, rem = [], []
    for p_state in podcast_states:
        change = p_state.get_change_between(device_id, since, until)
        if change == "subscribe":
            add.append(p_state.ref_url)
        elif change == "unsubscribe":
            rem.append(p_state.ref_url)

    return add, rem


def podcasts_for_states(podcast_states):
    """ returns the podcasts corresponding to the podcast states """

    podcast_ids = [state.podcast for state in podcast_states]
    podcasts = Podcast.objects.filter(id__in=podcast_ids)
    podcasts = {podcast.id.hex: podcast for podcast in podcasts}
    return podcasts.values()
