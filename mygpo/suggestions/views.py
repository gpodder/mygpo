from django.contrib.auth.decorators import login_required
from django.views.decorators.vary import vary_on_cookie
from django.views.decorators.cache import never_cache, cache_control

from mygpo.suggestions.models import PodcastSuggestion
from mygpo.podcasts.models import Podcast
from mygpo.api import APIView

import logging
logger = logging.getLogger(__name__)


class BlacklistSuggestion(APIView):

    def post(self, request, blacklisted_podcast):
        user = request.user

        logger.info('Removing suggestion of "{podcast}" for "{user}"'.format(
            podcast=blacklisted_podcast, user=user))

        suggestion = PodcastSuggestion.objects.filter(suggested_to=user,
                                                      podcast=blacklisted_podcast)\
                                              .update(deleted=True)

        # TODO
        return {
            'blacklisted_podcast': blacklisted_podcast,
        }


class SuggestionsList(APIView):
    @vary_on_cookie
    @cache_control(private=True)
    @login_required
    def get(self, request):
        user = request.user
        suggestions = Podcast.objects.filter(podcastsuggestion__suggested_to=user,
                                             podcastsuggestion__deleted=False)

        return {
            'suggestions': suggestions,
        }
