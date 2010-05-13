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

from django.contrib.auth.models import User
from mygpo.api.models import Podcast, Episode, Subscription
from mygpo.data.models import PodcastTag

def avg_update_interval(podcast):
    """
    returns the average interval between episodes for a given podcast
    """
    unique_timestamps = Episode.objects.filter(podcast=p, timestamp__isnull=False).order_by('timestamp').values('timestamp').distinct()
    c = unique_timestamps.count()
    t1 = unique_timestamps[0]['timestamp']
    t2 = unique_timestamps[c-1]['timestamp']
    return max(1, (t2 - t1).days / c)


def calc_similar_podcasts(podcast):
    """
    calculates and returns a list of podcasts that seem to be similar
    to the given one.

    Probably an expensive operation
    """
    tags = [t.tag for t in PodcastTag.objects.filter(podcast=podcast).only('tag').distinct()]
    users = User.objects.filter(subscription__podcast=podcast).only('id').distinct()
    subscribed = Subscription.objects.filter(user__in=users).only('podcast')
    podcast_list = {}
    for s in subscribed:
        if s.podcast == podcast:
            continue
        podcast_list[s.podcast] = podcast_list.get(s.podcast, 0) + 1

    for p in podcast_list.iterkeys():
        ps_tags = [t.tag for t in PodcastTag.objects.filter(podcast=p).only('tag').distinct()]
        matching_tags = filter(lambda t: t in tags, ps_tags)
        podcast_list[p] = podcast_list[p] * max(len(matching_tags), 1)

    l = list(podcast_list.iteritems())
    l.sort(key=lambda (p, count): count, reverse=True)
    return l


