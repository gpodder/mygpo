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

from mygpo.api.models import Podcast, Episode, Subscription
from mygpo.data.models import PodcastTag
from django.db.models import Sum, Count, Avg
from collections import defaultdict
import math

def get_source_weights():
    categories = [x['source'] for x in PodcastTag.objects.filter().values('source').distinct()]
    total_weights = {}
    for c in categories:
        tags = PodcastTag.objects.filter(source=c)
        total = tags.aggregate(total_weight=Sum('weight'))['total_weight']
        number = tags.aggregate(count=Count('weight'))['count']
        avg = float(total) / number
        total_weights[c] = 1. / avg

    return total_weights


def get_weighted_tags(podcast, source_weights):

    tags = defaultdict(int)
    for t in PodcastTag.objects.filter(podcast=podcast):
        tag = t.tag

        # promote more prominent tags of a podcast, demote less-prominent
        src_avg = PodcastTag.objects.filter(podcast=podcast, source=t.source).aggregate(weight=Avg('weight'))['weight']

        tags[tag] = tags[tag] + t.weight / src_avg * source_weights[t.source]

    try:
        subscriber_factor = math.log10(podcast.subscriber_count())
    except ValueError:
        # 0 subscribers
        subscriber_factor = 0

    for t in tags.iterkeys():
        tags[t] = tags[t] * subscriber_factor

    return tags


def get_weighted_group_tags(group, source_weights):

    podcast_tags = []

    for p in group.podcasts():
        podcast_tags.append(get_weighted_tags(p, source_weights))

    tags = reduce(lambda x, y: x+y, [x.keys() for x in podcast_tags])

    max_tags = {}
    for tag in tags:
        max_tags[tag] = max([x[tag] for x in podcast_tags])

    return max_tags


