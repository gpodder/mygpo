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

from collections import defaultdict
from itertools import cycle
import random

from django.core.cache import cache

from mygpo.data.mimetype import get_type, CONTENT_TYPES
from mygpo.core.models import Podcast, Episode
from mygpo.users.models import EpisodeUserState, Device
from mygpo.decorators import repeat_on_conflict
from datetime import timedelta

try:
    import simplejson as json
except ImportError:
    import json


def get_random_picks(languages=None):
    """ Returns random podcasts for the given language """

    if not languages:
        for podcast in Podcast.random():
            yield podcast

    counts = cache.get('podcast-language-counts')
    if not counts:
        counts = get_podcast_count_for_language()
        cache.set('podcast-language-counts', counts, 60*60)


    # extract positive counts of all languages in language param
    counts = filter(lambda (l, c): l in languages and c > 0, counts.items())

    for lang, count in cycle(counts):
        skip = random.randint(0, count-1)

        for podcast in Podcast.for_language(lang, skip=skip, limit=1):
            yield podcast



def get_podcast_count_for_language():
    """ Returns a the number of podcasts for each language """

    counts = defaultdict(int)

    db = Podcast.get_db()
    r = db.view('core/podcasts_by_language',
        reduce = True,
        group_level = 1,
    )

    counts.update( dict( (x['key'][0], x['value']) for x in r) )
    return counts



def get_device(user, uid, undelete=True):
    """
    Loads or creates the device indicated by user, uid.

    If the device has been deleted and undelete=True, it is undeleted.
    """

    @repeat_on_conflict(['user'])
    def _get(user, uid, undelete):

        device = user.get_device_by_uid(uid)

        if not device:
            device = Device(uid=uid)
            user.devices.append(device)
            user.save()

        elif device.deleted and undeleted:
            device.deleted = False
            user.set_device(device)
            user.save()

        return device

    return _get(user=user, uid=uid, undelete=undelete)


def get_favorites(user):
    favorites = EpisodeUserState.view('users/favorite_episodes_by_user', key=user.id)
    ids = [res['value'] for res in favorites]
    episodes = Episode.get_multi(ids)
    return episodes
