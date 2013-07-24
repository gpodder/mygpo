from mygpo.core.proxy import proxy_object
from mygpo.db.couchdb.user import get_num_listened_episodes
from mygpo.db.couchdb.podcast import podcasts_to_dict


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
    """ Sorts podcasts by the percentage of listened episodes

    Adds the attributes percent_listened and episodes_listened to the podcasts

    Cost: 1 DB query """

    def __init__(self, podcasts, user):
        super(PodcastPercentageListenedSorter, self).__init__(podcasts)
        self.user = user


    def _sort(self):

        SORT_KEY = lambda podcast: podcast.percent_listened

        counts = dict(get_num_listened_episodes(self.user))
        for podcast in self.podcasts:
            c = counts.get(podcast.get_id(), 0)
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
        if change == 'subscribe':
            add.append( p_state.ref_url )
        elif change == 'unsubscribe':
            rem.append( p_state.ref_url )

    return add, rem


def podcasts_for_states(podcast_states):
    """ returns the podcasts corresponding to the podcast states """

    podcast_ids = [state.podcast for state in podcast_states]
    podcasts = podcasts_to_dict(podcast_ids)

    for state in podcast_states:
        podcast = proxy_object(podcasts[state.podcast], url=state.ref_url)
        podcasts[state.podcast] = podcast

    return podcasts.values()
