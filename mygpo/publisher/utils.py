from collections import namedtuple, defaultdict
from datetime import timedelta, datetime, time

from mygpo.podcasts.models import Episode
from mygpo.utils import daterange
from mygpo.history.models import EpisodeHistoryEntry
from mygpo.history.stats import playcounts_timerange
from mygpo.publisher.models import PublishedPodcast


ListenerData = namedtuple('ListenerData', 'date playcount episode')

def listener_data(podcasts, start_date=datetime(2010, 1, 1),
                  leap=timedelta(days=1)):
    """ Returns data for the podcast listener timeseries

    An iterator with data for each day (starting from either the first released
    episode or the earliest play-event) is returned, where each day is
    reresented by a ListenerData tuple. """
    # index episodes by releaes-date
    episodes = Episode.objects.filter(podcast__in=podcasts,
                                      released__gt=start_date)
    episodes = {e.released.date(): e for e in episodes}

    history = EpisodeHistoryEntry.objects\
                                 .filter(episode__podcast__in=podcasts,
                                         timestamp__gte=start_date)\
    # contains play-counts, indexed by date {date: play-count}
    play_counts = playcounts_timerange(history)

    # we start either at the first episode-release or the first listen-event
    events = list(episodes.keys()) + list(play_counts.keys())

    if not events:
        # if we don't have any events, stop
        return

    start = min(events)
    for date in daterange(start, leap=leap):
        playcount = play_counts.get(date, 0)
        episode = episodes.get(date, None)
        yield ListenerData(date, playcount, episode)


def episode_listener_data(episode, start_date=datetime(2010, 1, 1),
                          leap=timedelta(days=1)):
    """ Returns data for the episode listener timeseries

    An iterator with data for each day (starting from the first event
    is returned, where each day is represented by a ListenerData tuple """
    history = EpisodeHistoryEntry.objects\
                                 .filter(episode=episode,
                                         timestamp__gte=start_date)\
    # contains play-counts, indexed by date {date: play-count}
    play_counts = playcounts_timerange(history)

    # we start either at the episode-release or the first listen-event
    events = list(play_counts.keys()) + \
             [episode.released.date()] if episode.released else []

    if not events:
        return

    # we always start at the first listen-event
    start = min(events)
    for date in daterange(start, leap=leap):
        playcount = play_counts.get(date, 0)
        e = episode if (episode.released.date() == date) else None
        yield ListenerData(date, playcount, e)


def subscriber_data(podcasts):
    coll_data = defaultdict(int)

    # TODO

    return []

    # TODO. rewrite
    for podcast in podcasts:
        create_entry = lambda r: (r.timestamp.strftime('%y-%m'), r.subscriber_count)

        subdata = [podcast.subscribers]

        data = dict(map(create_entry, subdata))

        for k in data:
            coll_data[k] += data[k]

    # create a list of {'x': label, 'y': value}
    coll_data = sorted([dict(x=a, y=b) for (a, b) in coll_data.items()], key=lambda x: x['x'])

    return coll_data


def check_publisher_permission(user, podcast):
    """ Checks if the user has publisher permissions for the given podcast """

    if not user.is_authenticated:
        return False

    if user.is_staff:
        return True

    return PublishedPodcast.objects.filter(publisher=user, podcast=podcast).exists()
