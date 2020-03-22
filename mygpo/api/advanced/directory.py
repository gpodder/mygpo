import json

from django.http import Http404
from django.http.response import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib.sites.requests import RequestSite
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
from django.shortcuts import get_object_or_404

from mygpo.podcasts.models import Podcast, Episode
from mygpo.utils import parse_range, normalize_feed_url
from mygpo.directory.tags import Topics
from mygpo.web.utils import get_episode_link_target, get_podcast_link_target
from mygpo.web.logo import get_logo_url
from mygpo.subscriptions.models import SubscribedPodcast
from mygpo.decorators import cors_origin
from mygpo.categories.models import Category
from mygpo.api.httpresponse import JsonResponse
from mygpo.data.tasks import update_podcasts
from mygpo.decorators import allowed_methods


@csrf_exempt
@cache_page(60 * 60 * 24)
@cors_origin()
def top_tags(request, count):
    count = parse_range(count, 1, 100, 100)
    tag_cloud = Topics(count, num_cat=0)
    resp = list(map(category_data, tag_cloud.tagcloud))
    return JsonResponse(resp)


@csrf_exempt
@cache_page(60 * 60 * 24)
@cors_origin()
def tag_podcasts(request, tag, count):
    count = parse_range(count, 1, 100, 100)
    try:
        category = Category.objects.get(tags__tag=tag)

    except Category.DoesNotExist:
        return JsonResponse([])

    domain = RequestSite(request).domain
    entries = category.entries.all().prefetch_related(
        'podcast', 'podcast__slugs', 'podcast__urls'
    )[:count]
    resp = [podcast_data(entry.podcast, domain) for entry in entries]
    return JsonResponse(resp)


@cache_page(60 * 60)
@cors_origin()
def podcast_info(request):
    url = normalize_feed_url(request.GET.get('url', ''))

    # 404 before we query for url, because query would complain
    # about missing param
    if not url:
        raise Http404

    podcast = get_object_or_404(Podcast, urls__url=url)
    domain = RequestSite(request).domain
    resp = podcast_data(podcast, domain)

    return JsonResponse(resp)


@cache_page(60 * 60)
@cors_origin()
def episode_info(request):
    podcast_url = normalize_feed_url(request.GET.get('podcast', ''))
    episode_url = normalize_feed_url(request.GET.get('url', ''))

    # 404 before we query for url, because query would complain
    # about missing parameters
    if not podcast_url or not episode_url:
        raise Http404

    try:
        query = Episode.objects.filter(
            podcast__urls__url=podcast_url, urls__url=episode_url
        )
        episode = query.select_related('podcast').get()
    except Episode.DoesNotExist:
        raise Http404

    domain = RequestSite(request).domain

    resp = episode_data(episode, domain)
    return JsonResponse(resp)


@csrf_exempt
@allowed_methods(['POST'])
@cors_origin()
def add_podcast(request):
    # TODO what if the url doesn't have a valid podcast?
    url = normalize_feed_url(json.loads(request.body.decode('utf-8')).get('url', ''))

    # 404 before we query for url, because query would complain
    # about missing param
    if not url:
        raise Http404

    try:
        # podcast exists, redirects
        Podcast.objects.get(urls__url=url)
        api_podcast_info_path = reverse('api-podcast-info')
        return HttpResponseRedirect(f'{api_podcast_info_path}?url={url}')
    except Podcast.DoesNotExist:
        # podcast doesn't exist, add new podcast
        res = update_podcasts.delay([url])
        response = HttpResponse(status=202)
        job_status_path = reverse(
            'api-add-podcast-status', kwargs={"job_id": res.task_id}
        )
        response['Location'] = f'{job_status_path}?url={url}'
        return response


@csrf_exempt
@allowed_methods(['GET'])
@cors_origin()
def add_podcast_status(request, job_id):
    url = request.GET.get('url', '')
    result = update_podcasts.AsyncResult(job_id)
    resp = {'id': str(job_id), 'type': 'create-podcast', 'url': url}

    if not result.ready():
        resp['status'] = 'pending'
    elif result.successful():
        resp['status'] = 'successful'
        resp['podcast'] = f'/api/2/data/podcast.json?url={url}'
    elif result.failed():
        resp['status'] = 'unsuccessful'
        resp['error'] = 'feed could not be parsed'

    return JsonResponse(resp)


def podcast_data(obj, domain, scaled_logo_size=64):
    if obj is None:
        raise ValueError('podcast should not be None')

    if isinstance(obj, SubscribedPodcast):
        url = obj.ref_url
        podcast = obj.podcast
    else:
        podcast = obj
        url = podcast.url

    subscribers = podcast.subscribers

    scaled_logo_url = get_logo_url(podcast, scaled_logo_size)

    return {
        "url": url,
        "title": podcast.title,
        "author": podcast.author,
        "description": podcast.description,
        "subscribers": subscribers,
        "logo_url": podcast.logo_url,
        "scaled_logo_url": 'http://%s%s' % (domain, scaled_logo_url),
        "website": podcast.link,
        "mygpo_link": 'http://%s%s' % (domain, get_podcast_link_target(podcast)),
    }


def episode_data(episode, domain, podcast=None):

    podcast = podcast or episode.podcast

    data = {
        "title": episode.title,
        "url": episode.url,
        "podcast_title": podcast.title if podcast else '',
        "podcast_url": podcast.url if podcast else '',
        "description": episode.description,
        "website": episode.link,
        "mygpo_link": 'http://%(domain)s%(res)s'
        % dict(domain=domain, res=get_episode_link_target(episode, podcast))
        if podcast
        else '',
    }

    if episode.released:
        data['released'] = episode.released.strftime('%Y-%m-%dT%H:%M:%S')
    else:
        data['released'] = ''

    return data


def category_data(category):
    return dict(
        title=category.clean_title, tag=category.tag, usage=category.num_entries
    )
