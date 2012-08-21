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

from mygpo.core.models import Podcast
from mygpo.users.models import PodcastUserState

try:
    from collections import Counter
except ImportError:
    from mygpo.counter import Counter


def calc_similar_podcasts(podcast, num=20):
    """
    calculates and returns a list of podcasts that seem to be similar
    to the given one.

    Probably an expensive operation
    """

    db = PodcastUserState.get_db()

    res = db.view('subscriptions/by_podcast',
            startkey    = [podcast.get_id(), None, None],
            endkey      = [podcast.get_id(), {}, {}],
            group       = True,
            group_level = 2,
            stale       = 'update_after',
        )

    users = (r['key'][1] for r in res)

    podcasts = Counter()


    for user_id in users:
        subscribed = db.view('subscriptions/by_user',
                startkey    = [user_id, True, None, None],
                endkey      = [user_id, True, {}, {}],
                group       = True,
                group_level = 3,
                stale       = 'update_after',
            )
        user_subscriptions = set(r['key'][2] for r in subscribed)
        user_counter = Counter(user_subscriptions)
        podcasts.update(user_counter)


    return podcasts.most_common(num)
