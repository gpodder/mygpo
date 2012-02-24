from datetime import datetime, timedelta

import gevent

from django.shortcuts import render
from django.views.generic.base import View
from django.utils.decorators import method_decorator

from mygpo.api import backend
from mygpo.share.models import PodcastList
from mygpo.users.models import User
from mygpo.users.models import HistoryEntry
from mygpo.decorators import requires_token
from mygpo.web.utils import fetch_episode_data
from mygpo.users.subscriptions import PodcastPercentageListenedSorter
from mygpo.web.views import GeventView



class UserpageView(GeventView):
    """ Shows the profile page for a user """

    @method_decorator(requires_token(token_name='userpage_token',
                denied_template='userpage-denied.html'))
    def get(self, request, username):

        user = User.get_user(username)
        month_ago = datetime.today() - timedelta(days=31)

        context_funs = {
            'lists': gevent.spawn(self.get_podcast_lists, user),
            'subscriptions': gevent.spawn(self.get_subscriptions, user),
            'recent_episodes': gevent.spawn(self.get_recent_episodes, user),
            'seconds_played_total': gevent.spawn(self.get_seconds_played_total, user),
            'seconds_played_month': gevent.spawn(self.get_seconds_played_since, user, month_ago),
            'favorite_episodes': gevent.spawn(self.get_favorite_episodes, user),
            'num_played_episodes_total': gevent.spawn(self.get_played_episodes_total, user),
            'num_played_episodes_month': gevent.spawn(self.get_played_episodes_since, user, month_ago),
        }

        context = {'page_user': user}
        context.update(self.get_context(context_funs))

        return render(request, 'userpage.html', context)


    def get_podcast_lists(self, user):
        return list(PodcastList.for_user(user._id))


    def get_subscriptions(self, user):
        subscriptions = user.get_subscribed_podcasts()
        return PodcastPercentageListenedSorter(subscriptions, user)


    def get_recent_episodes(self, user):
        recent_episodes = list(user.get_latest_episodes())
        return fetch_episode_data(recent_episodes)


    def get_seconds_played_total(self, user):
        return user.get_seconds_played()


    def get_seconds_played_since(self, user, since):
        return user.get_seconds_played(since=since)


    def get_favorite_episodes(self, user):
        favorite_episodes = backend.get_favorites(user)
        return fetch_episode_data(favorite_episodes)


    def get_played_episodes_total(self, user):
        return user.get_num_played_episodes()


    def get_played_episodes_since(self, user, since):
        return user.get_num_played_episodes(since=since)
