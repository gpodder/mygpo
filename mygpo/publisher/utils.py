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
from datetime import timedelta, date

from django.db.models import Avg, Count
from django.contrib.auth.models import User

from mygpo.utils import daterange
from mygpo.core.models import Podcast
from mygpo.api.models import Episode, EpisodeAction
from mygpo.web.utils import flatten_intervals
from mygpo.api.constants import DEVICE_TYPES
from mygpo import migrate


def listener_data(podcasts, start_date=date(2010, 1, 1), leap=timedelta(days=1)):
    episode_actions = EpisodeAction.objects.filter(
            episode__podcast__in=podcasts,
            timestamp__gte=start_date,
            action='play').order_by('timestamp').values('timestamp')

    if len(episode_actions) == 0:
        return []

    start = episode_actions[0]['timestamp']

    # pre-calculate episode list, make it index-able by release-date
    episodes = Episode.objects.filter(podcast__in=podcasts)
    episodes = filter(lambda e: e.timestamp, episodes)
    episodes = dict([(e.timestamp.date(), e) for e in episodes])

    days = []
    for d in daterange(start, leap=leap):
        next = d + leap

        get_listeners = lambda p: p.listener_count_timespan(d, next)
        listeners = map(get_listeners, podcasts)
        listener_sum = sum(listeners)

        episode = episodes[d.date()] if d.date() in episodes else None

        days.append(dict(date=d, listeners=listener_sum, episode=episode))

    return days


def episode_listener_data(episode, start_date=date(2010, 1, 1), leap=timedelta(days=1)):
    episodes = EpisodeAction.objects.filter(episode=episode,
            timestamp__gte=start_date).order_by('timestamp').values('timestamp')
    if len(episodes) == 0:
        return []

    start = episodes[0]['timestamp']

    intervals = []
    for d in daterange(start, leap=leap):
        next = d + leap

        listeners = episode.listener_count_timespan(d, next)
        released_episode = episode if episode.timestamp and episode.timestamp >= d and episode.timestamp <= next else None
        intervals.append(dict(date=d, listeners=listeners, episode=released_episode))

    return intervals


def subscriber_data(podcasts):
    coll_data = collections.defaultdict(int)

    for p in podcasts:
        podcast = Podcast.for_oldid(p.id)

        create_entry = lambda r: (r.timestamp.strftime('%y-%m'), r.subscriber_count)
        data = dict(map(create_entry, podcast.subscribers))

        for k in data:
            coll_data[k] += data[k]

    # create a list of {'x': label, 'y': value}
    coll_data = sorted([dict(x=a, y=b) for (a, b) in coll_data.items()], key=lambda x: x['x'])

    return coll_data


def check_publisher_permission(user, podcast):
    if user.is_staff:
        return True

    p = migrate.get_or_migrate_podcast(podcast)
    u = migrate.get_or_migrate_user(user)
    if p.get_id() in user.published_podcasts():
        return True

    return False


def device_stats(podcasts):
    l = EpisodeAction.objects.filter(episode__podcast__in=podcasts).values('device__type').annotate(count=Count('id'))
    l = filter(lambda x: int(x['count']) > 0, l)
    l = map(lambda x: (x['device__type'], x['count']), l)
    return dict(l)


def episode_heatmap(episode, max_part_num=30, min_part_length=10):
    """
    Generates "Heatmap Data" for the given episode

    The episode is split up in parts having max 'max_part_num' segments which
    are all of the same length, minimum 'min_part_length' seconds.

    For each segment, the number of users that have played it (at least
    partially) is calculated and returned
    """

    episode_actions = EpisodeAction.objects.filter(episode=episode, action='play')

    duration = episode.duration or episode_actions.aggregate(duration=Avg('total'))['duration']

    if not duration:
        return [0], 0

    part_length = max(min_part_length, int(duration / max_part_num))

    part_num = int(duration / part_length)

    heatmap = [0]*part_num

    user_ids = [x['user'] for x in episode_actions.values('user').distinct()]
    for user_id in user_ids:
        actions = episode_actions.filter(user__id=user_id, playmark__isnull=False, started__isnull=False)
        if actions.exists():
            played_parts = flatten_intervals(actions)
            user_heatmap = played_parts_to_heatmap(played_parts, part_length, part_num)
            heatmap = [sum(pair) for pair in zip(heatmap, user_heatmap)]

    return heatmap, part_length


def played_parts_to_heatmap(played_parts, part_length, part_count):
    """
    takes the (flattened) parts of an episode that a user has played, and
    generates a heatmap data for this user.

    The result is a list with part_count elements, each having a value
    of either 0 (user has not played that part) or 1 (user has at least
    partially played that part)

    >>> played_parts_to_heatmap([{'start': 0, 'end': 3}, {'start': 6, 'end': 8}], 1, 10)
    [1, 1, 1, 1, 0, 1, 1, 1, 1, 0]
    """
    parts = [0]*part_count

    if not played_parts:
        return parts

    part_iter = iter(played_parts)
    current_part = part_iter.next()

    for i in range(0, part_count):
        part = i * part_length
        while current_part['end'] < part:
            try:
                current_part = part_iter.next()
            except StopIteration:
                return parts

        if current_part['start'] <= (part + part_length) and current_part['end'] >= part:
            parts[i] += 1

    return parts


def colour_repr(val, max_val, colours):
    """
    returns a color representing the given value within a color gradient.

    The color gradient is given by a list of (r, g, b) tupels. The value
    is first located within two colors (of the list) and then approximated
    between these two colors, based on its position within this segment.
    """
    if len(colours) == 1:
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
