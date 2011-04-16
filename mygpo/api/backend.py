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

from mygpo.api.models import Device, Podcast, EpisodeToplistEntry
from mygpo.data.mimetype import get_type, CONTENT_TYPES
from mygpo.core import models
from mygpo.users.models import EpisodeUserState
from datetime import timedelta

try:
    import simplejson as json
except ImportError:
    import json


def get_podcasts_for_languages(languages=None, podcast_query=Podcast.objects.all()):
    if not languages:
        return Podcast.objects.all()

    regex = '^(' + '|'.join(languages) + ')'
    return podcast_query.filter(language__regex=regex)



def get_random_picks(languages=None, recent_days=timedelta(days=7)):
    all_podcasts    = Podcast.objects.all().exclude(title='').order_by('?')
    lang_podcasts   = get_podcasts_for_languages(languages, all_podcasts)

    if lang_podcasts.count() > 0:
        return lang_podcasts
    else:
        return all_podcasts


def get_device(user, uid, undelete=True):
    """
    Loads or creates the device indicated by user, uid.

    If the device has been deleted and undelete=True, it is undeleted.
    """
    device, created = Device.objects.get_or_create(user=user, uid=uid)

    if device.deleted and undelete:
        device.deleted = False
        device.save()

    return device


def get_favorites(user):
    favorites = EpisodeUserState.view('users/favorite_episodes_by_user', key=user.id)
    ids = [res['value'] for res in favorites]
    episodes = models.Episode.get_multi(ids)
    return [e.get_old_obj() for e in episodes]
