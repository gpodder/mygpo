from django.shortcuts import get_object_or_404

from mygpo.api import APIView, RequestException
from mygpo.podcasts.models import Podcast, Episode
from mygpo.usersettings.models import UserSettings
from mygpo.api.httpresponse import JsonResponse


class SettingsAPI(APIView):
    """Settings API

    wiki.gpodder.org/wiki/Web_Services/API_2/Settings"""

    def get(self, request, username, scope):
        """Get settings for scope object"""
        user = request.user
        scope = self.get_scope(request, scope)
        settings = UserSettings.objects.get_for_scope(user, scope)
        return JsonResponse(settings.as_dict())

    def post(self, request, username, scope):
        """Update settings for scope object"""
        user = request.user
        scope = self.get_scope(request, scope)
        actions = self.parsed_body(request)
        settings = UserSettings.objects.get_for_scope(user, scope)
        resp = self.update_settings(settings, actions)
        return JsonResponse(resp)

    def get_scope(self, request, scope):
        """Get the scope object"""
        if scope == "account":
            return None

        if scope == "device":
            uid = request.GET.get("device", "")
            return request.user.client_set.get(uid=uid)

        episode_url = request.GET.get("episode", "")
        podcast_url = request.GET.get("podcast", "")

        if scope == "podcast":
            return get_object_or_404(Podcast, urls__url=podcast_url)

        if scope == "episode":
            podcast = get_object_or_404(Podcast, urls__url=podcast_url)
            return get_object_or_404(Episode, podcast=podcast, urls__url=episode_url)

        raise RequestException("undefined scope %s" % scope)

    def update_settings(self, settings, actions):
        """Update the settings according to the actions"""
        for key, value in actions.get("set", {}).items():
            settings.set_setting(key, value)

        for key in actions.get("remove", []):
            settings.del_setting(key)

        settings.save()
        return settings.as_dict()
