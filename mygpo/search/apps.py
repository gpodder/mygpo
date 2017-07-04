from django.apps import AppConfig, apps
from django.db.models.signals import post_save

from mygpo.search.index import index_podcast


class SearchConfig(AppConfig):
    name = 'mygpo.search'
    verbose_name = 'Search'

    def ready(self):
        Podcast = apps.get_model('podcasts.Podcast')
        post_save.connect(index_podcast, sender=Podcast)
        pass
