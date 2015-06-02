#
# This file is part of my.gpodder.org.
#
# my.gpodder.org is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# my.gpodder.org is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public
# License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with my.gpodder.org. If not, see <http://www.gnu.org/licenses/>.
#

from collections import namedtuple, defaultdict
from datetime import timedelta, datetime, time

from mygpo.podcasts.models import Episode
from mygpo.utils import daterange, flatten
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

    if not user.is_authenticated():
        return False

    if user.is_staff:
        return True

    return PublishedPodcast.objects.filter(publisher=user, podcast=podcast).exists()


def colour_repr(val, max_val, colours):
    """
    returns a color representing the given value within a color gradient.

    The color gradient is given by a list of (r, g, b) tupels. The value
    is first located within two colors (of the list) and then approximated
    between these two colors, based on its position within this segment.
    """
    if len(colours) == 1:
        return colours[0]

    if max_val == 0:
        return colours[0]

    # calculate position in the gradient; defines the segment
    pos = float(val) / max_val
    colour_nr1 = min(len(colours)-1, int(pos * (len(colours)-1)))
    colour_nr2 = min(len(colours)-1, colour_nr1+1)
    colour1 = colours[ colour_nr1 ]
    colour2 = colours[ colour_nr2 ]

    r1, g1, b1 = colour1
    r2, g2, b2 = colour2

    # determine bounds of segment
    lower_bound = float(max_val) / (len(colours)-1) * colour_nr1
    upper_bound = min(max_val, lower_bound + float(max_val) / (len(colours)-1))

    # position within the segment
    percent = (val - lower_bound) / upper_bound

    r_step = r2 - r1
    g_step = g2 - g1
    b_step = b2 - b1

    return (r1 + r_step * percent, g1 + g_step * percent, b1 + b_step * percent)
