from django.db.models import Count
from mygpo.api.models import Subscription, Podcast
from mygpo.data.models import PodcastTag


def podcast_group_entry(group, subscriber_count=None):
    from mygpo.search.models import SearchEntry

    if not subscriber_count:
        subscriber_count = Subscription.objects.filter(podcast__group=group).values('user').distinct().count()

    entry = SearchEntry()
    entry.text = group.title
    entry.obj_type = 'podcast_group'
    entry.obj_id = group.id

    podcasts = Podcast.objects.filter(group=group)
    entry.tags = tag_string(PodcastTag.objects.filter(podcast__in=podcasts))

    entry.priority = subscriber_count

    return entry


def podcast_entry(podcast, subscriber_count=None):
    from mygpo.search.models import SearchEntry

    if not subscriber_count:
        subscriber_count = Subscription.objects.filter(podcast=podcast).values('user').distinct().count()

    entry = SearchEntry()
    entry.text = podcast.title
    entry.obj_type = 'podcast'
    entry.obj_id = podcast.id

    entry.tags = tag_string(PodcastTag.objects.filter(podcast=podcast))

    entry.priority = subscriber_count

    return entry


def tag_string(tags, max_length=200):
    """
    returns a string of the most-assigned tags

    tags is expected to be a PodcastTag QuerySet
    """
    tags = PodcastTag.objects.top_tags(tags)
    return ','.join([t['tag'] for t in tags])[:max_length]

