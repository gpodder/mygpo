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
from mygpo.core.models import Podcast
from mygpo.users.models import PodcastUserState
from mygpo.api.models import Episode
from mygpo.utils import flatten

try:
    from collections import Counter
except ImportError:
    from mygpo.counter import Counter


def avg_update_interval(podcast):
    """
    returns the average interval between episodes for a given podcast
    """
    unique_timestamps = Episode.objects.filter(podcast=p, timestamp__isnull=False).order_by('timestamp').values('timestamp').distinct()
    c = unique_timestamps.count()
    t1 = unique_timestamps[0]['timestamp']
    t2 = unique_timestamps[c-1]['timestamp']
    return max(1, (t2 - t1).days / c)


def calc_similar_podcasts(podcast, num=20):
    """
    calculates and returns a list of podcasts that seem to be similar
    to the given one.

    Probably an expensive operation
    """

    db = PodcastUserState.get_db()

    res = db.view('users/subscriptions_by_podcast',
            startkey    = [podcast.get_id(), None, None],
            endkey      = [podcast.get_id(), {}, {}],
            group       = True,
            group_level = 2,
        )

    users = (r['key'][1] for r in res)

    podcasts = Counter()


    for user_oldid in users:
        subscribed = db.view('users/subscribed_podcasts_by_user',
                startkey    = [user_oldid, True, None, None],
                endkey      = [user_oldid, True, {}, {}],
                group       = True,
                group_level = 3,
            )
        user_subscriptions = set(r['key'][2] for r in subscribed)
        user_counter = Counter(user_subscriptions)
        podcasts.update(user_counter)


    return podcasts.most_common(num)
