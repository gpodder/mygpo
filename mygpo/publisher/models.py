from django.db import models
from django.contrib.auth.models import User
from mygpo.api.models import Podcast

class PodcastPublisher(models.Model):
    user = models.ForeignKey(User)
    podcast = models.ForeignKey(Podcast)

    class Meta:
        unique_together = ('user', 'podcast')
        db_table = 'publisher'
        managed = False
