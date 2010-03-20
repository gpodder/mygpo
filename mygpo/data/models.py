from django.db import models
from mygpo.api.models import Podcast, Episode

class HistoricPodcastData(models.Model):
    podcast = models.ForeignKey(Podcast)
    date = models.DateField()
    subscriber_count = models.IntegerField()

    class Meta:
        db_table = 'historic_podcast_data'
        unique_together = ('podcast', 'date')


class HistoryEpisodeData(models.Model):
    episode = models.ForeignKey(Episode)
    date = models.DateField()
    listener_count = models.IntegerField()

    class Meta:
        db_table = 'historic_episode_data'
        unique_together = ('episode', 'date')

