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

from datetime import timedelta, date
from mygpo.utils import daterange
from mygpo.api.models import Episode, EpisodeAction
from mygpo.data.models import HistoricPodcastData
from mygpo.web.utils import flatten_intervals
from mygpo.publisher.models import PodcastPublisher
from mygpo.api.constants import DEVICE_TYPES
from django.db.models import Avg
from django.contrib.auth.models import User


def listener_data(podcasts):
    day = timedelta(1)

    # get start date
    d = date(2010, 1, 1)
    episode_actions = EpisodeAction.objects.filter(episode__podcast__in=podcasts, timestamp__gte=d, action='play').order_by('timestamp').values('timestamp')
    if len(episode_actions) == 0:
        return []

    start = episode_actions[0]['timestamp']

    # pre-calculate episode list, make it index-able by release-date
    episodes = {}
    for episode in Episode.objects.filter(podcast__in=podcasts):
        if episode.timestamp:
            episodes[episode.timestamp.date()] = episode

    days = []
    for d in daterange(start):
        next = d + timedelta(days=1)
        listener_sum = 0

        # this is faster than .filter(episode__podcast__in=podcasts)
        for p in podcasts:
            listeners = EpisodeAction.objects.filter(episode__podcast=p, timestamp__gte=d, timestamp__lt=next, action='play').values('user_id').distinct().count()
            listener_sum += listeners

        if d.date() in episodes:
            episode = episodes[d.date()]
        else:
            episode = None

        days.append({
            'date': d,
            'listeners': listener_sum,
            'episode': episode})

    return days


def episode_listener_data(episode):
    d = date(2010, 1, 1)
    leap = timedelta(days=1)

    episodes = EpisodeAction.objects.filter(episode=episode, timestamp__gte=d).order_by('timestamp').values('timestamp')
    if len(episodes) == 0:
        return []

    start = episodes[0]['timestamp']

    intervals = []
    for d in daterange(start, leap=leap):
        next = d + leap
        listeners = EpisodeAction.objects.filter(episode=episode, timestamp__gte=d, timestamp__lt=next).values('user_id').distinct().count()
        e = episode if episode.timestamp >= d and episode.timestamp <= next else None
        intervals.append({
            'date': d,
            'listeners': listeners,
            'episode': e})

    return intervals


def subscriber_data(podcasts):
    data = {}

    #this is fater than a subquery
    records = []
    for p in podcasts:
        records.extend(HistoricPodcastData.objects.filter(podcast=p).order_by('date'))

    for r in records:
        if r.date.day == 1:
            s = r.date.strftime('%y-%m')
            val = data.get(s, 0)
            data[s] = val + r.subscriber_count

    list = []
    for k, v in data.iteritems():
        list.append({'x': k, 'y': v})

    list.sort(key=lambda x: x['x'])

    return list


def check_publisher_permission(user, podcast):
    if user.is_staff:
        return True

    if PodcastPublisher.objects.filter(user=user, podcast=podcast).count() > 0:
        return True

    return False

def episode_list(podcast):
    episodes = Episode.objects.filter(podcast=podcast).order_by('-timestamp')
    for e in episodes:
        listeners = EpisodeAction.objects.filter(episode=e, action='play').values('user').distinct()
        e.listeners = listeners.count()

    return episodes


def device_stats(podcasts):
    res = {}
    for type in DEVICE_TYPES:
        c = 0

        # this is faster than a subquery
        for p in podcasts:
            c += EpisodeAction.objects.filter(episode__podcast=p, device__type=type[0]).values('user_id').distinct().count()
        if c > 0:
            res[type[1]] = c

    return res


def episode_heatmap(episode, max_part_num=50, min_part_length=10):
    """
    Generates "Heatmap Data" for the given episode

    The episode is split up in parts having max 'max_part_num' segments which
    are all of the same length, minimum 'min_part_length' seconds.

    For each segment, the number of users that have played it (at least
    partially) is calculated and returned
    """

    episode_actions = EpisodeAction.objects.filter(episode=episode, action='play')

    if episode.duration:
        duration = episode.duration
    else:
        duration = episode_actions.aggregate(duration=Avg('total'))['duration']

    if not duration:
        return [0], 0

    part_length = max(min_part_length, int(duration / max_part_num))

    part_num = int(duration / part_length)

    heatmap = [0]*part_num

    user_ids = [x['user'] for x in episode_actions.values('user').distinct()]
    for user_id in user_ids:
        user = User.objects.get(id=user_id)
        actions = episode_actions.filter(user=user, playmark__isnull=False, started__isnull=False)
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
            parts[i] = 1
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

