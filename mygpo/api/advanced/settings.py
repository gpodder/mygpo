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

from django.http import Http404
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator

from mygpo.core.models import Episode, Podcast
from mygpo.api.basic_auth import require_valid_user, check_username
from mygpo.users.models import PodcastUserState
from mygpo.api.advanced import AdvancedAPIEndpoint
from mygpo.api.exceptions import APIParameterException



class SettingsEndpoint(AdvancedAPIEndpoint):

    @method_decorator(require_valid_user)
    @method_decorator(check_username)
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        return super(SettingsEndpoint, self).dispatch(*args, **kwargs)

    def get(self, request, username, scope):
        base_obj, settings_obj = self.get_settings_obj(request, scope)
        return settings_obj.settings

    def post(self, request, username, scope):
        base_obj, settings_obj = self.get_settings_obj()
        actions = self.get_post_data(request)
        ret = self.update_settings(settings_obj, actions)
        base_obj.save()
        return ret


    def get_settings_obj(self, scope, request):

        if scope == 'account':
            return self.user_settings(request.user)

        if scope == 'device':
            return self.device_settings(request.user,
                    request.GET.get('device', '')
                )

        if scope == 'podcast':
            return self.podcast_settings(request.user,
                    request.GET.get('podcast', '')
                )

        if scope == 'episode':
            return self.episode_settings(request.user,
                    request.GET.get('episode', ''),
                    request.GET.get('podcast', '')
                )

        raise APIParameterException('undefined scope %s' % scope)


    def user_settings(user):
        return user, user


    def device_settings(user, uid):
        device = user.get_device_by_uid(uid)

        # get it from the user directly so that changes
        # to settings_obj are reflected in user (bug 1344)
        settings_obj = user.get_device_by_uid(uid)

        return user, settings_obj


    def podcast_settings(user, url):
        podcast = Podcast.for_url(url)
        if not podcast:
            raise Http404

        podcast_state = podcast.get_user_state(user)
        return podcast_state, podcast_state


    def episode_settings(user, url, podcast_url):
        episode = Episode.for_podcast_url(podcast_url, url)
        if episode is None:
            raise Http404

        episode_state = episode.get_user_state(user)
        return episode_state, episode_state


    def update_settings(self, obj, actions):
        for key, value in actions.get('set', {}).iteritems():
            obj.settings[key] = value

        for key in actions.get('remove', []):
            if key in obj.settings:
                del obj.settings[key]

        return obj.settings
