from datetime import datetime, timedelta

from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.template.defaultfilters import slugify
from django.contrib.sites.models import RequestSite
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import ugettext as _

from mygpo.api import backend
from mygpo.core.models import Podcast
from mygpo.core.proxy import proxy_object
from mygpo.api.simple import format_podcast_list
from mygpo.share.models import PodcastList
from mygpo.users.models import User
from mygpo.directory.views import search as directory_search
from mygpo.users.models import HistoryEntry
from mygpo.decorators import requires_token
from mygpo.web.utils import fetch_episode_data


@requires_token(token_name='userpage_token', denied_template='userpage-denied.html')
def show(request, username):

    user = User.get_user(username)

    # the lists that the user has created
    lists = list(PodcastList.for_user(user._id))

    # A top list of podcast subscriptions
    # - If we have episode actions, based on the # of actions, descending
    # - If no actions exist, based on the # of devices, descending
    subscriptions = list(user.get_subscribed_podcasts(sort='most_listened'))

    # A list of recently-listened episodes
    recent_episodes = list(user.get_latest_episodes())
    recent_episodes = HistoryEntry.fetch_data(user, recent_episodes)

    # Minutes listened this week (this month) -> based on play actions
    seconds_played_total = user.get_seconds_played()
    month_ago = datetime.today() - timedelta(days=31)
    seconds_played_month = user.get_seconds_played(since=month_ago)

    # Favorite Episodes
    favorite_episodes = backend.get_favorites(user)
    favorite_episodes = fetch_episode_data(favorite_episodes)

    # Number of played episodes
    num_played_episodes_total = user.get_num_played_episodes()
    num_played_episodes_month = user.get_num_played_episodes(since=month_ago)

    return render_to_response('userpage.html', {
            'page_user': user,
            'lists': lists,
            'subscriptions': subscriptions,
            'recent_episodes': recent_episodes,
            'seconds_played_total': seconds_played_total,
            'seconds_played_month': seconds_played_month,
            'favorite_episodes': favorite_episodes,
            'num_played_episodes_total': num_played_episodes_total,
            'num_played_episodes_month': num_played_episodes_month,
        }, context_instance=RequestContext(request))
