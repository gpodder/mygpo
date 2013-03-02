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

import time
from datetime import datetime

import dateutil.parser

from django.http import HttpResponseBadRequest, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache

from mygpo.core import models
from mygpo.api.httpresponse import JsonResponse
from mygpo.api.exceptions import ParameterMissing
from mygpo.api.sanitizing import sanitize_url
from mygpo.api.backend import get_device
from mygpo.users.models import Chapter
from mygpo.utils import parse_time
from mygpo.decorators import allowed_methods
from mygpo.core.json import json
from mygpo.api.basic_auth import require_valid_user, check_username
from mygpo.db.couchdb.episode import episode_for_podcast_url
from mygpo.db.couchdb.episode_state import episode_state_for_user_episode


@csrf_exempt
@require_valid_user
@check_username
@never_cache
@allowed_methods(['POST', 'GET'])
def chapters(request, username):

    now = datetime.utcnow()
    now_ = int(time.mktime(now.timetuple()))

    if request.method == 'POST':
        req = json.loads(request.body)

        if not 'podcast' in req:
            return HttpResponseBadRequest('Podcast URL missing')

        if not 'episode' in req:
            return HttpResponseBadRequest('Episode URL missing')

        podcast_url = req.get('podcast', '')
        episode_url = req.get('episode', '')
        update_urls = []

        # podcast sanitizing
        s_podcast_url = sanitize_url(podcast_url)
        if s_podcast_url != podcast_url:
            req['podcast'] = s_podcast_url
            update_urls.append((podcast_url, s_podcast_url))

        # episode sanitizing
        s_episode_url = sanitize_url(episode_url, 'episode')
        if s_episode_url != episode_url:
            req['episode'] = s_episode_url
            update_urls.append((episode_url, s_episode_url))

        if (s_podcast_url != '') and (s_episode_url != ''):
            try:
                update_chapters(req, request.user)
            except ParameterMissing, e:
                return HttpResponseBadRequest(e)

        return JsonResponse({
            'update_url': update_url,
            'timestamp': now_
            })

    elif request.method == 'GET':
        if not 'podcast' in request.GET:
            return HttpResponseBadRequest('podcast URL missing')

        if not 'episode' in request.GET:
            return HttpResponseBadRequest('Episode URL missing')

        podcast_url = request.GET['podcast']
        episode_url = request.GET['episode']

        since_ = request.GET.get('since', None)
        try:
            since = datetime.fromtimestamp(float(since_)) if since_ else None
        except ValueError:
            return HttpResponseBadRequest('since-value is not a valid timestamp')

        podcast_url = sanitize_url(podcast_url)
        episode_url = sanitize_url(episode_url, 'episode')
        episode = episode_for_podcast_url(podcast_url, episode_url)

        if episode is None:
            raise Http404

        e_state = episode_state_for_user_episode(request.user, episode)

        chapterlist = sorted(e_state.chapters, key=lambda c: c.start)

        if since:
            chapterlist = filter(lambda c: c.created >= since, chapters)

        chapters = []
        for c in chapterlist:
            if c.device is not None:
                device = request.user.get_device(c.device)
                device_uid = device.uid
            else:
                device_uid = None

            chapters.append({
                'start': c.start,
                'end':   c.end,
                'label': c.label,
                'advertisement': c.advertisement,
                'timestamp': c.created,
                'device': device_uid
                })

        return JsonResponse({
            'chapters': chapters,
            'timestamp': now_
            })


def update_chapters(req, user):
    podcast_url = sanitize_url(req['podcast'])
    episode_url = sanitize_url(req['episode'], 'episode')

    episode = episode_for_podcast_url(podcast_url, episode_url,
            create=True)

    e_state = episode_state_for_user_episode(request.user, episode)

    device = None
    if 'device' in req:
        device = get_device(request.user, req['device'],
                request.META.get('HTTP_USER_AGENT', ''), undelete=True)

    timestamp = dateutil.parser.parse(req['timestamp']) if 'timestamp' in req else datetime.utcnow()

    new_chapters = parse_new_chapters(request.user, req.get('chapters_add', []))
    rem_chapters = parse_rem_chapters(req.get('chapters_remove', []))

    e_state.update_chapters(new_chapters, rem_chapters)



def parse_new_chapters(user, chapters):
    for c in chapters:
        if not 'start' in c:
            raise ParameterMissing('start parameter missing')
        start = parse_time(c['start'])

        if not 'end' in c:
            raise ParameterMissing('end parameter missing')
        end = parse_time(c['end'])

        label = c.get('label', '')
        adv = c.get('advertisement', False)

        device_uid = c.get('device', None)
        if device_uid:
            device_id = get_device(user, device_uid,
                    request.META.get('HTTP_USER_AGENT', ''), undelete=True).id
        else:
            device_id = None

        chapter = Chapter()
        chapter.device = device_id
        chapter.created = timestamp
        chapter.start = start
        chapter.end = end
        chapter.label = label
        chapter.advertisement = adv

        yield chapter


def parse_rem_chapters(chapers):
    for c in chapters:
        if not 'start' in c:
            raise ParameterMissing('start parameter missing')
        start = parse_time(c['start'])

        if not 'end' in c:
            raise ParameterMissing('end parameter missing')
        end = parse_time(c['end'])

        yield (start, end)
