from datetime import datetime, timedelta

from functools import partial

from django.shortcuts import render
from django.views.generic.base import View
from django.utils.decorators import method_decorator
from django.contrib.sites.models import RequestSite

from mygpo.podcasts.models import Episode
from mygpo.users.models import User
from mygpo.users.models import HistoryEntry
from mygpo.users.settings import FLATTR_USERNAME
from mygpo.decorators import requires_token
from mygpo.web.utils import fetch_episode_data
from mygpo.users.subscriptions import PodcastPercentageListenedSorter
from mygpo.web.views import GeventView
from mygpo.db.couchdb.episode_state import favorite_episode_ids_for_user
from mygpo.db.couchdb.user import get_latest_episodes, \
         get_num_played_episodes, get_seconds_played
from mygpo.db.couchdb.podcastlist import podcastlists_for_user



class UserpageView(GeventView):
    """ Shows the profile page for a user """

    @method_decorator(requires_token(token_name='userpage_token',
                denied_template='userpage-denied.html'))
    def get(self, request, username):

        user = User.get_user(username)
        month_ago = datetime.today() - timedelta(days=31)
        site = RequestSite(request)

        context_funs = {
            'lists': partial(self.get_podcast_lists, user),
            'subscriptions': partial(self.get_subscriptions, user),
            'recent_episodes': partial(self.get_recent_episodes, user),
            'seconds_played_total': partial(self.get_seconds_played_total, user),
            'seconds_played_month': partial(self.get_seconds_played_since, user, month_ago),
            'favorite_episodes': partial(self.get_favorite_episodes, user),
            'num_played_episodes_total': partial(self.get_played_episodes_total, user),
            'num_played_episodes_month': partial(self.get_played_episodes_since, user, month_ago),
        }

        context = {
            'page_user': user,
            'flattr_username': user.get_wksetting(FLATTR_USERNAME),
            'site': site.domain,
            'subscriptions_token': user.get_token('subscriptions_token'),
            'favorite_feeds_token': user.get_token('favorite_feeds_token'),
        }
        context.update(self.get_context(context_funs))

        return render(request, 'userpage.html', context)


    def get_podcast_lists(self, user):
        return podcastlists_for_user(user._id)


    def get_subscriptions(self, user):
        subscriptions = user.get_subscribed_podcasts()
        return PodcastPercentageListenedSorter(subscriptions, user)


    def get_recent_episodes(self, user):
        recent_episodes = get_latest_episodes(user)
        return fetch_episode_data(recent_episodes)


    def get_seconds_played_total(self, user):
        return get_seconds_played(user)


    def get_seconds_played_since(self, user, since):
        return get_seconds_played(user, since=since)


    def get_favorite_episodes(self, user):
        favorite_ids = favorite_episode_ids_for_user(user)
        favorites = Episode.objects.get(id__in=favorite_ids)
        return fetch_episode_data(favorites)


    def get_played_episodes_total(self, user):
        return get_num_played_episodes(user)


    def get_played_episodes_since(self, user, since):
        return get_num_played_episodes(user, since=since)
