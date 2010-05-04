import datetime
from haystack import indexes
from haystack import site
from mygpo.api.models import Podcast, Episode


class PodcastIndex(indexes.SearchIndex):

    text = indexes.CharField(document=True, use_template=True)

    def get_queryset(self):
        """Used when the entire index for model is updated."""
        return Podcast.objects.all().exclude(title='')


class EpisodeIndex(indexes.SearchIndex):

    text = indexes.CharField(document=True, use_template=True)

    def get_queryset(self):
        return Episode.objects.all().exclude(title='')


site.register(Podcast, PodcastIndex)
site.register(Episode, EpisodeIndex)
