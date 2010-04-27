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
from mygpo.publisher.models import PodcastPublisher
from mygpo.api.constants import DEVICE_TYPES


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


