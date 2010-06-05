from django.db.models import Count
from mygpo.api.models import Subscription, Podcast
from mygpo.data.models import PodcastTag
from mygpo.search.models import SearchEntry
import shlex

def simple_search(q):
    qs = SearchEntry.objects.all()
    for query in shlex.split(q):
        qs = qs.filter(text__icontains=query)

    return qs.order_by('-priority')

def podcast_group_entry(group, subscriber_count=None):

    if not subscriber_count:
        subscriber_count = Subscription.objects.filter(podcast__group=group).values('user').distinct().count()

    entry = SearchEntry()
    entry.text = group.title
    entry.obj_type = 'podcast_group'
    entry.obj_id = group.id

    podcasts = Podcast.objects.filter(group=group)
    tags = PodcastTag.objects.filter(podcast__in=podcasts).annotate(count=Count('podcast')).order_by('count')
    tag_string = ','.join([t.tag for t in tags])[:200]
    entry.tags = tag_string

    entry.priority = subscriber_count

    return entry


def podcast_entry(podcast, subscriber_count=None):

    if not subscriber_count:
        subscriber_count = Subscription.objects.filter(podcast=podcast).values('user').distinct().count()

    entry = SearchEntry()
    entry.text = podcast.title
    entry.obj_type = 'podcast'
    entry.obj_id = podcast.id

    tags = PodcastTag.objects.filter(podcast=podcast).annotate(count=Count('podcast')).order_by('count')
    tag_string = ','.join([t.tag for t in tags])[:200]
    entry.tags = tag_string

    entry.priority = subscriber_count

    return entry

