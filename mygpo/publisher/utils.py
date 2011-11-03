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

import collections
from datetime import timedelta, datetime, time

from django.db.models import Avg, Count
from django.contrib.auth.models import User

from mygpo.utils import daterange, flatten
from mygpo.core.models import Podcast
from mygpo.api.constants import DEVICE_TYPES
from mygpo import migrate


def listener_data(podcasts, start_date=datetime(2010, 1, 1), leap=timedelta(days=1)):
    """ Returns data for the podcast listener timeseries

    An iterator with data for each day (starting from either the first released
    episode or the earliest listen-event) is returned, where each day
    is reresented by a dictionary

     * date: the day
     * listeners: the number of listeners on that day
     * episode: (one of) the episode(s) released on that day
    """

    # pre-calculate episode list, make it index-able by release-date
    episodes = (podcast.get_episodes(since=start_date) for podcast in podcasts)
    episodes = flatten(episodes)
    episodes = dict((e.released.date(), e) for e in episodes)

    listeners = [ list(p.listener_count_timespan(start=start_date))
                    for p in podcasts ]
    listeners = filter(None, listeners)

    # we start either at the first episode-release or the first listen-event
    events = []

    if episodes.keys():
        events.append(min(episodes.keys()))

    if listeners:
        events.append(min([l[0][0] for l in listeners]))

    if not events:
        return

    start = min(events)

    for d in daterange(start, leap=leap):

        listener_sum = 0
        for l in listeners:
            if not l:
                continue

            day, count = l[0]
            if day == d:
                listener_sum += count
                l.pop(0)

        episode = episodes[d] if d in episodes else None

        yield dict(date=d, listeners=listener_sum, episode=episode)



def episode_listener_data(episode, start_date=datetime(2010, 1, 1), leap=timedelta(days=1)):
    """ Returns data for the episode listener timeseries

    An iterator with data for each day (starting from the first listen-event)
    is returned, where each day is represented by a dictionary

     * date: the day
     * listeners: the number of listeners on that day
     * episode: the episode, if it was released on that day, otherwise None
    """

    listeners = list(episode.listener_count_timespan(start=start_date))

    if not listeners:
        return

    # we always start at the first listen-event
    start = listeners[0][0]
    start = datetime.combine(start, time())

    for d in daterange(start, leap=leap):
        next = d + leap

        if listeners and listeners[0] and listeners[0][0] == d.date():
            day, l = listeners.pop(0)
        else:
            l = 0

        released = episode.released and episode.released >= d and episode.released <= next
        released_episode = episode if released else None

        yield dict(date=d, listeners=l, episode=released_episode)


def subscriber_data(podcasts):
    coll_data = collections.defaultdict(int)

    for podcast in podcasts:
        create_entry = lambda r: (r.timestamp.strftime('%y-%m'), r.subscriber_count)
        data = dict(map(create_entry, podcast.get_all_subscriber_data()))

        for k in data:
            coll_data[k] += data[k]

    # create a list of {'x': label, 'y': value}
    coll_data = sorted([dict(x=a, y=b) for (a, b) in coll_data.items()], key=lambda x: x['x'])

    return coll_data


def check_publisher_permission(user, podcast):
    if user.is_staff:
        return True

    u = migrate.get_or_migrate_user(user)
    return (podcast.get_id() in u.published_objects)


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
