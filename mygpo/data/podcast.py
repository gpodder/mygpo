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

from mygpo.db.couchdb.podcast_state import subscribed_users, \
         subscribed_podcast_ids_by_user_id

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

    users = subscribed_users(podcast)

    podcasts = Counter()

    for user_id in users:
        user_subscriptions = subscribed_podcast_ids_by_user_id(user_id)
        user_counter = Counter(user_subscriptions)
        podcasts.update(user_counter)

    return podcasts.most_common(num)
