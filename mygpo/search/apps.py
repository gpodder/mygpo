from django.apps import AppConfig
from django.db.models.signals import post_save

from mygpo.podcasts.models import Podcast
from mygpo.search.index import index_podcast


class SearchConfig(AppConfig):
    name = 'mygpo.search'
    verbose_name = 'Search'

    def ready(self):
        post_save.connect(index_podcast, sender=Podcast)
