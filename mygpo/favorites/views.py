from django.views.decorators.vary import vary_on_cookie
from django.views.decorators.cache import never_cache, cache_control
from django.contrib.auth.decorators import login_required

from mygpo.podcasts.models import Podcast
from mygpo.favorites.models import FavoriteEpisode
from mygpo.api import APIView


class FavoriteEpisodes(APIView):
    @vary_on_cookie
    @cache_control(private=True)
    @login_required
    def get(self, request):
        user = request.user

        favorites = FavoriteEpisode.episodes_for_user(user)

        recently_listened = last_played_episodes(user)

        favfeed = FavoriteFeed(user)
        feed_url = favfeed.get_public_url(site.domain)

        podcast = Podcast.objects.filter(urls__url=feed_url).first()

        token = request.user.profile.favorite_feeds_token

        return {
            'episodes': favorites,
            'feed_token': token,
            'site': site,
            'podcast': podcast,
            'recently_listened': recently_listened,
        }

