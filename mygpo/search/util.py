from mygpo.data.models import PodcastTag

def tag_string(tags, max_length=200):
    """
    returns a string of the most-assigned tags

    tags is expected to be a PodcastTag QuerySet
    """
    tags = PodcastTag.objects.top_tags(tags)
    return ','.join([t['tag'] for t in tags])[:max_length]

