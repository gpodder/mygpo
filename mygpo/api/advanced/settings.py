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

from django.http import HttpResponseBadRequest, Http404, HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
from django.shortcuts import get_object_or_404

from mygpo.decorators import allowed_methods, cors_origin
from mygpo.podcasts.models import Podcast, Episode
from mygpo.utils import parse_request_body
from mygpo.api.basic_auth import require_valid_user, check_username
from mygpo.api.httpresponse import JsonResponse
from mygpo.users.models import PodcastUserState, DeviceDoesNotExist
from mygpo.db.couchdb import get_main_database, get_userdata_database
from mygpo.db.couchdb.podcast_state import podcast_state_for_user_podcast
from mygpo.db.couchdb.episode_state import episode_state_for_user_episode


@csrf_exempt
@require_valid_user
@check_username
@never_cache
@allowed_methods(['GET', 'POST'])
@cors_origin()
def main(request, username, scope):

    db = get_main_database()
    udb = get_userdata_database()

    def user_settings(user):
        return user, user, db

    def device_settings(user, uid):
        device = user.get_device_by_uid(uid)

        # get it from the user directly so that changes
        # to settings_obj are reflected in user (bug 1344)
        settings_obj = user.get_device_by_uid(uid)

        return user, settings_obj, db

    def podcast_settings(user, url):
        podcast = get_object_or_404(Podcast, urls__url=url)
        obj = podcast_state_for_user_podcast(user, podcast)
        return obj, obj, udb

    def episode_settings(user, url, podcast_url):
        try:
            episode = Episode.objects.filter(podcast__urls__url=podcast_url,
                                             urls__url=url).get()
        except Episode.DoesNotExist:
            raise Http404

        episode_state = episode_state_for_user_episode(user, episode)
        return episode_state, episode_state, udb

    models = dict(
            account = lambda: user_settings(request.user),
            device  = lambda: device_settings(request.user, request.GET.get('device', '')),
            podcast = lambda: podcast_settings(request.user, request.GET.get('podcast', '')),
            episode = lambda: episode_settings(request.user, request.GET.get('episode', ''), request.GET.get('podcast', ''))
        )


    if scope not in models.keys():
        return HttpResponseBadRequest('undefined scope %s' % scope)

    try:
        base_obj, settings_obj, db = models[scope]()
    except DeviceDoesNotExist as e:
        return HttpResponseNotFound(str(e))

    if request.method == 'GET':
        return JsonResponse( settings_obj.settings )

    elif request.method == 'POST':
        actions = parse_request_body(request)
        ret = update_settings(settings_obj, actions)
        db.save_doc(base_obj)
        return JsonResponse(ret)


def update_settings(obj, actions):
    for key, value in actions.get('set', {}).iteritems():
        obj.settings[key] = value

    for key in actions.get('remove', []):
        if key in obj.settings:
            del obj.settings[key]

    return obj.settings
