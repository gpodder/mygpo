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

def listener_data(podcast):
    d = date(2010, 1, 1)
    day = timedelta(1)
    episodes = EpisodeAction.objects.filter(episode__podcast=podcast, timestamp__gte=d).order_by('timestamp').values('timestamp')
    if len(episodes) == 0:
        return []

    start = episodes[0]['timestamp']

    days = []
    for d in daterange(start):
        next = d + timedelta(days=1)
        listeners = EpisodeAction.objects.filter(episode__podcast=podcast, timestamp__gte=d, timestamp__lt=next).values('user_id').distinct().count()
        e = Episode.objects.filter(podcast=podcast, timestamp__gte=d, timestamp__lt=next)
        episode = e[0] if e.count() > 0 else None
        days.append({
            'date': d,
            'listeners': listeners,
            'episode': episode})

    return days


def subscriber_data(podcast):
    data = {}
    records = HistoricPodcastData.objects.filter(podcast=podcast).order_by('date')
    for r in records:
        if r.date.day == 1:
            s = r.date.strftime('%y-%m')
            data[s] = r.subscriber_count

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

