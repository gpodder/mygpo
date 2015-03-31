from django.http import HttpResponse, HttpResponseRedirect, \
        HttpResponseForbidden
from django.core.cache import cache
from django.views.decorators.cache import never_cache, cache_control
from django.views.decorators.vary import vary_on_cookie
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404

from mygpo.podcasts.models import PodcastGroup, Podcast, Episode
from mygpo.publisher.auth import require_publisher, is_publisher
from mygpo.publisher.utils import listener_data, episode_listener_data, \
         check_publisher_permission, subscriber_data
from mygpo.web.heatmap import EpisodeHeatmap
from mygpo.web.views.episode import (slug_decorator as episode_slug_decorator,
    id_decorator as episode_id_decorator)
from mygpo.podcasts.views import (slug_decorator as podcast_slug_decorator,
    id_decorator as podcast_id_decorator)
from mygpo.web.utils import normalize_twitter
from mygpo.data.tasks import update_podcasts
from mygpo.decorators import requires_token
from mygpo.pubsub.models import HubSubscription
from mygpo.api import APIView


class PublishedPodcasts(APIView):
    @vary_on_cookie
    @cache_control(private=True)
    def get(self, request):
        podcasts =  Podcast.objects\
                           .filter(publishedpodcast__publisher=request.user)\
                           .prefetch_related('slugs')
        return {
            'podcasts': podcasts,
        }


class PodcastTimelineData(APIView):

    @require_publisher
    def get(self, request, podcast):
        timeline_data = listener_data([podcast])
        return {
            'timeline': timeline_data,
        }


class PodcastSubscriptionData(APIView):

    @require_publisher
    def get(self, request, podcast):
        subscription_data = subscriber_data([podcast])[-20:]
        return {
            'subscriptions': subscription_data,
        }


class PodcastHeatmap(APIView):

    @require_publisher
    def get(self, request, podcast):
        heatmap = EpisodeHeatmap(podcast)
        return {
            'heatmap': heatmap,
        }


class PodcastPubSub(APIView):
    @vary_on_cookie
    @cache_control(private=True)
    @require_publisher
    def get(self, request, podcast):

        try:
            pubsubscription = HubSubscription.objects.get(topic_url=podcast.url)
        except HubSubscription.DoesNotExist:
            pubsubscription = None

        return {
            'pubsubscription': pubsubscription,
        }


class GroupTimelineData(APIView):
    @vary_on_cookie
    @cache_control(private=True)
    @require_publisher
    def get(self, request, group):

        timeline_data = listener_data(podcasts)

        return {
            'timeline': timeline_data,
        }

class GroupSubscriptions(APIView):

    def get(self, request, group):
        subscription_data = list(subscriber_data(podcasts))[-20:]

        return {
            'subscriptions': subscription_data,
        }


class SchedulePodcastUpdate(APIView):

    @vary_on_cookie
    @cache_control(private=True)
    @require_publisher
    def post(self, request, podcast):

        if not check_publisher_permission(request.user, podcast):
            return HttpResponseForbidden()

        update_podcasts.delay([podcast.url])
        return # success / task?


class PodcastPublisherData(APIView):
    @vary_on_cookie
    @cache_control(private=True)
    @require_publisher
    def put(self, request, podcast):
        twitter = normalize_twitter(request.POST.get('twitter', ''))
        podcast.twitter = twitter
        podcast.save()
        return # success


@never_cache
@requires_token(token_name='publisher_update_token')
def update_published_podcasts(request, username):
    User = get_user_model()
    user = get_object_or_404(User, username=username)
    published_podcasts = [pp.podcast for pp in user.publishedpodcast_set.all()]
    update_podcasts.delay([podcast.url for podcast in published_podcasts])
    return HttpResponse('Updated:\n' + '\n'.join([p.url for p in published_podcasts]), content_type='text/plain')


class EpisodeTimelineData(APIVIew):
    @require_publisher
    @vary_on_cookie
    @cache_control(private=True)
    def get(self, request, episode):

        timeline_data = list(episode_listener_data(episode))
        return {
            'timeline': timeline_data,
        }


class EpisodeHeatmap(APIView):

    def get(self, request, episode):
        heatmap = EpisodeHeatmap(episode.podcast, episode,
                                 duration=episode.duration)
        return {
            'heatmap': heatmap,
        }


class SetEpisodeSlug(APIView):
    @require_publisher
    @never_cache
    def post(self, request, episode):
        """ sets a new "main" slug, and moves the existing to the merged slugs """

        new_slug = request.POST.get('slug')
        podcast = episode.podcast

        if new_slug:
            # remove the new slug from other episodes (of the same podcast)
            other_episodes = Episode.objects.filter(
                podcast=podcast,
                slugs__slug=new_slug,
                slugs__content_type=ContentType.objects.get_for_model(Episode),
            )

            for other_episode in other_episodes:

                if other_episode == episode:
                    continue

                other_episode.remove_slug(new_slug)

        episode.set_slug(new_slug)

        # TODO: we should use better cache invalidation
        cache.clear()
        return # success
