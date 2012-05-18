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

from functools import partial
from itertools import imap as map
from collections import defaultdict
from datetime import datetime
import time

import dateutil.parser

from django.http import Http404
from django.contrib.sites.models import get_current_site
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator

from mygpo.api.constants import EPISODE_ACTION_TYPES
from mygpo.api.httpresponse import JsonResponse
from mygpo.api.sanitizing import sanitize_append
from mygpo.api.advanced import AdvancedAPIEndpoint
from mygpo.api.backend import get_device, get_favorites, \
         clean_episode_action_data, episode_data
from mygpo.utils import parse_time, format_time, parse_bool, get_timestamp
from mygpo.decorators import repeat_on_conflict
from mygpo.core.models import Podcast, Episode
from mygpo.users.models import EpisodeAction, EpisodeUserState
from mygpo.api.basic_auth import require_valid_user, check_username
from mygpo.api.exceptions import ParameterMissing
from mygpo.users.models import Chapter


class ChaptersEndpoint(AdvancedAPIEndpoint):

    @method_decorator(require_valid_user)
    @method_decorator(check_username)
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        return super(ChapterEndpoint, self).dispatch(*args, **kwargs)


    def post(self, request, username):
        now = datetime.utcnow()
        now_ = int(time.mktime(now.timetuple()))

        req = self.get_post_data(request)

        if not 'podcast' in req:
            return ParameterMissing('Podcast URL missing')

        if not 'episode' in req:
            return ParameterMissing('Episode URL missing')

        podcast_url = req.get('podcast', '')
        episode_url = req.get('episode', '')
        update_urls = []

        s_podcast_url = sanitize_append(podcast_url, 'podcast', update_urls)
        s_episode_url = sanitize_append(episode_url, 'episode', update_urls)

        if s_podcast_url and s_episode_url:
            self.update_chapters(req, request.user, s_podcast_url,
                    s_episode_url)

        return {
            'update_url': update_url,
            'timestamp': now_
            }



    def get(self, request, username):

        now = datetime.utcnow()
        now_ = int(time.mktime(now.timetuple()))
        update_url = []

        podcast_url = request.GET.get('podcast', None)
        episode_url = request.GET.get('episode', None)

        if not podcast_url:
            raise ParameterMissing('podcast URL missing')

        if not episode_url:
            raise ParameterMissing('Episode URL missing')

        since_ = request.GET.get('since', None)
        try:
            since = datetime.fromtimestamp(float(since_)) if since_ else None
        except ValueError:
            return APIParameterException('since-value is not a valid timestamp')

        podcast_url = sanitize_append(podcast_url, 'podcast', update_url)
        episode_url = sanitize_append(episode_url, 'episode', update_url)
        episode = Episode.for_podcast_url(podcast_url, episode_url)

        if episode is None:
            raise Http404

        e_state = episode.get_user_state(request.user)

        chapterlist = sorted(e_state.chapters, key=lambda c: c.start)

        if since:
            chapterlist = filter(lambda c: c.created >= since, chapters)

        chapter_to_json = partial(self.chapter_to_json, request.user)
        chapters = map(chapter_to_json, chapterlist)

        return {
            'chapters': chapters,
            'timestamp': now_,
            'update_url': update_url,
            }


    def chapter_to_json(self, user, chapter):
        if chapter.device is not None:
            device_uid = user.get_device(c.device).uid
        else:
            device_uid = None

        return {
            'start': c.start,
            'end':   c.end,
            'label': c.label,
            'advertisement': c.advertisement,
            'timestamp': c.created,
            'device': device_uid
            }


    def update_chapters(self, req, user, podcast_url, episode_url):

        episode = Episode.for_podcast_url(podcast_url, episode_url,
                create=True)

        e_state = episode.get_user_state(user)

        device = None
        if 'device' in req:
            device = get_device(user, req['device'],
                    request.META.get('HTTP_USER_AGENT', ''), undelete=True)

        if 'timestamp' in req:
            timestamp = dateutil.parser.parse(req['timestamp'])
        else:
            timestamp = datetime.utcnow()

        parse_new_chapter = partial(self.parse_new_chapters, user)
        new_chapters = map(parse_new_chapters, req.get('chapters_add', []))

        rem_chapters = map(self.parse_rem_chapters, req.get('chapters_remove', []))

        e_state.update_chapters(new_chapters, rem_chapters)



    def parse_new_chapters(self, user, c):
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

        return chapter


    def parse_rem_chapters(self, c):
        if not 'start' in c:
            raise ParameterMissing('start parameter missing')
        start = parse_time(c['start'])

        if not 'end' in c:
            raise ParameterMissing('end parameter missing')
        end = parse_time(c['end'])

        yield (start, end)




# keys that are allowed in episode actions
EPISODE_ACTION_KEYS = ('position', 'episode', 'action', 'device', 'timestamp',
                       'started', 'total', 'podcast')



class EpisodeActionEndpoint(AdvancedAPIEndpoint):

    @method_decorator(require_valid_user)
    @method_decorator(check_username)
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        return super(EpisodeActionEndpoint, self).dispatch(*args, **kwargs)



    def post(self, request, username, version=1):

        now = datetime.now()
        now_ = get_timestamp(now)
        ua_string = request.META.get('HTTP_USER_AGENT', '')

        actions = self.get_post_data(request)

        update_urls = self.update_episodes(request.user, actions, now,
                ua_string)

        return {'timestamp': now_, 'update_urls': update_urls}


    def get(self, request, username, version=1):

        version = int(version)
        now = datetime.now()
        ua_string = request.META.get('HTTP_USER_AGENT', '')

        podcast_url= request.GET.get('podcast', None)
        device_uid = request.GET.get('device', None)
        since_     = request.GET.get('since', None)
        aggregated = parse_bool(request.GET.get('aggregated', False))

        try:
            since = datetime.fromtimestamp(float(since_)) if since_ else None
        except ValueError:
            raise APIParameterException('since-value is not a valid timestamp')

        if podcast_url:
            podcast = Podcast.for_url(podcast_url)
            if not podcast:
                raise Http404
        else:
            podcast = None

        if device_uid:
            device = request.user.get_device_by_uid(device_uid)

            if not device or device.deleted:
                raise Http404
        else:
            device = None

        changes = self.get_episode_changes(request.user, podcast, device,
                since, now, aggregated, version)

        return changes



    def convert_position(action):
        """ convert position parameter for API 1 compatibility """
        pos = getattr(action, 'position', None)
        if pos is not None:
            action.position = format_time(pos)
        return action



    def get_episode_changes(self, user, podcast, device, since,
            until, aggregated, version):

        devices = dict( (dev.id, dev.uid) for dev in user.devices )

        args = {}
        if podcast is not None:
            args['podcast_id'] = podcast.get_id()

        if device is not None:
            args['device_id'] = device.id

        actions = EpisodeAction.filter(user._id, since, until, **args)

        if version == 1:
            actions = map(convert_position, actions)

        clean_data = partial(clean_episode_action_data, devices=devices)

        actions = filter(None, map(clean_data, actions))

        if aggregated:
            actions = dict( (a['episode'], a) for a in actions ).values()

        until_ = get_timestamp(until)

        return {'actions': actions, 'timestamp': until_}



    def update_episodes(self, user, actions, now, ua_string):
        update_urls = []

        grouped_actions = defaultdict(list)

        # group all actions by their episode
        for action in actions:

            podcast_url = action['podcast']
            podcast_url = sanitize_append(podcast_url, 'podcast', update_urls)
            if podcast_url == '':
                continue

            episode_url = action['episode']
            episode_url = sanitize_append(episode_url, 'episode', update_urls)
            if episode_url == '':
                continue

            act = self.parse_episode_action(action, user, now, ua_string)
            grouped_actions[ (podcast_url, episode_url) ].append(act)

        # load the episode state only once for every episode
        for (p_url, e_url), action_list in grouped_actions.iteritems():
            episode_state = EpisodeUserState.for_ref_urls(user, p_url, e_url)

            self.update_episode_actions(episode_state=episode_state,
                action_list=action_list)

        return update_urls



    @repeat_on_conflict(['episode_state'])
    def update_episode_actions(self, episode_state, action_list):
        """ Adds actions to the episode state and saves if necessary """

        changed = False

        len1 = len(episode_state.actions)
        episode_state.add_actions(action_list)
        len2 = len(episode_state.actions)

        if len1 < len2:
            changed = True

        if changed:
            episode_state.save()

        return changed


    def parse_episode_action(self, action, user, now, ua_string):
        action_str  = action.get('action', None)
        if not valid_episodeaction(action_str):
            raise APIParameterException('invalid action %s' % action_str)

        new_action = EpisodeAction()

        new_action.action = action['action']

        if action.get('device', False):
            device = get_device(user, action['device'], ua_string)
            new_action.device = device.id

        if action.get('timestamp', False):
            new_action.timestamp = dateutil.parser.parse(action['timestamp'])
        else:
            new_action.timestamp = now

        new_action.timestamp = new_action.timestamp.replace(microsecond=0)

        new_action.started = action.get('started', None)
        new_action.playmark = action.get('position', None)
        new_action.total = action.get('total', None)

        return new_action



    def valid_episodeaction(self, action_type):
        return action_type in [t[0] for t in EPISODE_ACTION_TYPES]




class FavoritesEndpoint(AdvancedAPIEndpoint):

    @require_valid_user
    @check_username
    @never_cache
    def get(self, request, username):
        favorites = get_favorites(request.user)
        domain = get_current_site(request).domain
        e_data = lambda e: episode_data(e, domain)
        ret = map(e_data, favorites)
        return ret
