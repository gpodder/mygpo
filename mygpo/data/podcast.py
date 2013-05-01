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

from collections import Counter
import logging

from django.conf import settings

from mygpo.db.couchdb.podcast_state import subscribed_users, \
         subscribed_podcast_ids_by_user_id
from mygpo import pubsub

logger = logging.getLogger(__name__)


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


def subscribe_at_hub(podcast):
    """ Tries to subscribe to the given podcast at its hub """

    if not podcast.hub:
        return

    base_url = settings.DEFAULT_BASE_URL

    if not base_url:
        logger.warn('Could not subscribe to podcast {podcast} '
                    'at hub {hub} because DEFAULT_BASE_URL is not '
                    'set.'.format(podcast=podcast, hub=podcast.hub))
        return

    logger.info('subscribing to {podcast} at {hub}.'.format(podcast=podcast,
                                                           hub=podcast.hub))
    pubsub.subscribe(podcast.url, podcast.hub, base_url)
