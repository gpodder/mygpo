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
from mygpo.api.basic_auth import require_valid_user, check_username
from django.http import HttpResponseBadRequest
from mygpo.api.httpresponse import JsonResponse
from mygpo.api.exceptions import ParameterMissing
from mygpo.api.sanitizing import sanitize_url
from mygpo.api.models import Device, Podcast, Episode
from mygpo.users.models import Chapter
from datetime import datetime
from mygpo.utils import parse_time
from mygpo.decorators import allowed_methods
import dateutil.parser
from mygpo import migrate
from django.views.decorators.csrf import csrf_exempt

try:
    import simplejson as json
except ImportError:
    import json


@csrf_exempt
@require_valid_user
@check_username
@allowed_methods(['POST', 'GET'])
def chapters(request, username):

    now = datetime.utcnow()
    now_ = int(time.mktime(now.timetuple()))

    if request.method == 'POST':
        req = json.loads(request.raw_post_data)

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

        podcast = Podcast.objects.get(url=sanitize_url(podcast_url))
        episode = Episode.objects.get(url=sanitize_url(episode_url, 'episode'), podcast=podcast)

        new_episode = migrate.get_or_migrate_episode(episode)
        e_state = new_episode.get_user_state(request.user)

        new_user = migrate.get_or_migrate_user(request.user)

        chapterlist = sorted(e_state.chapters, key=lambda c: c.start)

        if since:
            chapterlist = filter(lambda c: c.created >= since, chapters)

        chapters = []
        for c in chapterlist:
            if c.device is not None:
                device = migrate.get_or_migrate_device(c.device)
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
    podcast, c = Podcast.objects.get_or_create(url=req['podcast'])
    episode, c = Episode.objects.get_or_create(url=req['episode'], podcast=podcast)

    new_episode = migrate.get_or_migrate_episode(episode)
    e_state = new_episode.get_user_state(request.user)

    device = None
    if 'device' in req:
        device, c = Device.objects.get_or_create(user=user, uid=req['device'])

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
            device = Device.objects.get(user=user, uid=device_uid)
            new_device = migrate.get_or_migrate_device(device)
            device_id = new_device.id
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
