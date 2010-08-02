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
from django.http import HttpResponseBadRequest, HttpResponseNotAllowed
from mygpo.api.httpresponse import JsonResponse
from django.shortcuts import get_object_or_404
from mygpo.api.models import Device, UserProfile, SubscriptionMeta, EpisodeSettings
from django.views.decorators.csrf import csrf_exempt
import json


@csrf_exempt
@require_valid_user
@check_username
def main(request, username, scope):

    models = dict(
            account = lambda: request.get_profile(),
            device  = lambda: get_object_or_404(Device, user=request.user, uid=request.GET.get('device', '')),
            podcast = lambda: SubscriptionMeta.objects.get_or_create(user=request.user,
                podcast__url=request.GET.get('podcast', ''))[0],
            episode = lambda: EpisodeSettings.objects.get_or_create(user=request.user,
                episode__url=request.GET.get('episode', ''), episode__podcast__url=request.GET.get('podcast', ''))[0]
        )


    if scope not in models.keys():
        return HttpResponseBadRequest()

    obj = models[scope]()

    if request.method == 'GET':
        return JsonResponse( obj.settings )
    elif request.method == 'POST':
        actions = json.loads(request.raw_post_data)
        return JsonResponse( update_settings(obj, actions) )

    else:
        return HttpResponseNotAllowed(['GET', 'POST'])


def update_settings(obj, actions):
    for key, value in actions.get('set', {}).iteritems():
        obj.settings[key] = value

    for key in actions.get('remove', []):
        if key in obj.settings:
            del obj.settings[key]

    return obj.settings

