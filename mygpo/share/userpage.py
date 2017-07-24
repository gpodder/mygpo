from datetime import datetime, timedelta

from django.shortcuts import render
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.sites.requests import RequestSite
from django.contrib.auth import get_user_model

from mygpo.podcasts.models import Episode
from mygpo.users.models import HistoryEntry
from mygpo.users.settings import FLATTR_USERNAME
from mygpo.subscriptions import get_subscribed_podcasts
from mygpo.decorators import requires_token
from mygpo.podcastlists.models import PodcastList
from mygpo.users.subscriptions import PodcastPercentageListenedSorter
from mygpo.history.stats import (num_played_episodes, last_played_episodes,
    seconds_played)
from mygpo.favorites.models import FavoriteEpisode


class UserpageView(View):
    """ Shows the profile page for a user """

    @method_decorator(requires_token(token_name='userpage_token',
                denied_template='userpage-denied.html'))
    def get(self, request, username):

        User = get_user_model()
        user = User.objects.get(username=username)
        month_ago = datetime.today() - timedelta(days=31)
        site = RequestSite(request)

        context = {
            'page_user': user,
            'flattr_username': user.profile.settings.get_wksetting(FLATTR_USERNAME),
            'site': site.domain,
            'subscriptions_token': user.profile.get_token('subscriptions_token'),
            'favorite_feeds_token': user.profile.get_token('favorite_feeds_token'),
            'lists': self.get_podcast_lists(user),
            'subscriptions': self.get_subscriptions(user),
            'recent_episodes': last_played_episodes(user),
            'seconds_played_total': seconds_played(user),
            'seconds_played_month': seconds_played(user, month_ago),
            'favorite_episodes': FavoriteEpisode.episodes_for_user(user),
            'num_played_episodes_total': num_played_episodes(user),
            'num_played_episodes_month': num_played_episodes(user, month_ago),
        }

        return render(request, 'userpage.html', context)


    def get_podcast_lists(self, user):
        return PodcastList.objects.filter(user=user)


    def get_subscriptions(self, user):
        subscriptions = [sp.podcast for sp in get_subscribed_podcasts(user)]
        return PodcastPercentageListenedSorter(subscriptions, user)
