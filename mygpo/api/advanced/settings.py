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

from mygpo.api.basic_auth import require_valid_user, check_username
from django.http import HttpResponseBadRequest, Http404
from mygpo.api.httpresponse import JsonResponse
from django.shortcuts import get_object_or_404
from mygpo.users.models import PodcastUserState
from mygpo.api.models import Device, Podcast
from django.views.decorators.csrf import csrf_exempt
from mygpo.decorators import allowed_methods
from mygpo import migrate
from mygpo.core.models import Episode

try:
    import simplejson as json
except ImportError:
    import json


@csrf_exempt
@require_valid_user
@check_username
@allowed_methods(['GET', 'POST'])
def main(request, username, scope):

    def user_settings(user):
        obj = migrate.get_or_migrate_user(user)
        return obj, obj

    def device_settings(user, uid):
        device = get_object_or_404(Device, user=user, uid=uid)
        user = migrate.get_or_migrate_user(user)

        # This is a reference to a separate obj
        dev = migrate.get_or_migrate_device(device, user)

        # get it from the user directly so that changes
        # to settings_obj are reflected in user (bug 1344)
        settings_obj = user.get_device_by_uid(uid)

        return user, settings_obj

    def podcast_settings(user, url):
        old_p = get_object_or_404(Podcast, url=url)
        podcast = migrate.get_or_migrate_podcast(old_p)
        obj = PodcastUserState.for_user_podcast(user, podcast)
        return obj, obj

    def episode_settings(user, url, podcast_url):
        episode = Episode.for_podcast_url(podcast_url, url)
        if episode is None:
            raise Http404

        episode_state = episode.get_user_state(user)
        return episode_state, episode_state

    models = dict(
            account = lambda: user_settings   (request.user),
            device  = lambda: device_settings (request.user, request.GET.get('device', '')),
            podcast = lambda: podcast_settings(request.user, request.GET.get('podcast', '')),
            episode = lambda: episode_settings(request.user, request.GET.get('episode', ''), request.GET.get('podcast', ''))
        )


    if scope not in models.keys():
        return HttpResponseBadRequest('undefined scope %s' % scope)

    base_obj, settings_obj = models[scope]()

    if request.method == 'GET':
        return JsonResponse( settings_obj.settings )

    elif request.method == 'POST':
        actions = json.loads(request.raw_post_data)
        ret = update_settings(settings_obj, actions)
        base_obj.save()
        return JsonResponse(ret)


def update_settings(obj, actions):
    for key, value in actions.get('set', {}).iteritems():
        obj.settings[key] = value

    for key in actions.get('remove', []):
        if key in obj.settings:
            del obj.settings[key]

    return obj.settings

