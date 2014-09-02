from datetime import datetime, timedelta

from django.shortcuts import render
from django.views.generic.base import View
from django.utils.decorators import method_decorator
from django.contrib.sites.models import RequestSite
from django.contrib.auth import get_user_model

from mygpo.podcasts.models import Episode
from mygpo.users.models import HistoryEntry
from mygpo.users.settings import FLATTR_USERNAME
from mygpo.subscriptions import get_subscribed_podcasts
from mygpo.decorators import requires_token
from mygpo.podcastlists.models import PodcastList
from mygpo.users.subscriptions import PodcastPercentageListenedSorter
from mygpo.db.couchdb.episode_state import favorite_episode_ids_for_user
from mygpo.db.couchdb.user import get_latest_episode_ids, \
         get_num_played_episodes, get_seconds_played



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
            'flattr_username': user.profile.get_wksetting(FLATTR_USERNAME),
            'site': site.domain,
            'subscriptions_token': user.profile.get_token('subscriptions_token'),
            'favorite_feeds_token': user.profile.get_token('favorite_feeds_token'),
            'lists': self.get_podcast_lists(user),
            'subscriptions': self.get_subscriptions(user),
            'recent_episodes': self.get_recent_episodes(user),
            'seconds_played_total': self.get_seconds_played_total(user),
            'seconds_played_month': self.get_seconds_played_since( user, month_ago),
            'favorite_episodes': self.get_favorite_episodes(user),
            'num_played_episodes_total': self.get_played_episodes_total(user),
            'num_played_episodes_month': self.get_played_episodes_since(user, month_ago),
        }

        return render(request, 'userpage.html', context)


    def get_podcast_lists(self, user):
        return PodcastList.objects.filter(user=user)


    def get_subscriptions(self, user):
        subscriptions = [sp.podcast for sp in get_subscribed_podcasts(user)]
        return PodcastPercentageListenedSorter(subscriptions, user)


    def get_recent_episodes(self, user):
        recent_episode_ids = get_latest_episode_ids(user)
        recent_episodes = Episode.objects.filter(id__in=recent_episode_ids)\
                                         .select_related('podcast')\
                                         .prefetch_related('slugs',
                                                           'podcast__slugs')
        return recent_episodes


    def get_seconds_played_total(self, user):
        return get_seconds_played(user)


    def get_seconds_played_since(self, user, since):
        return get_seconds_played(user, since=since)


    def get_favorite_episodes(self, user):
        favorite_ids = favorite_episode_ids_for_user(user)
        favorites = Episode.objects.filter(id__in=favorite_ids)\
                                   .select_related('podcast')\
                                   .prefetch_related('slugs', 'podcast__slugs')
        return favorites


    def get_played_episodes_total(self, user):
        return get_num_played_episodes(user)


    def get_played_episodes_since(self, user, since):
        return get_num_played_episodes(user, since=since)
