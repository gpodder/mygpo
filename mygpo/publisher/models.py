""" This module contains models for the publisher pages """

from django.db import models
from django.conf import settings

from mygpo.podcasts.models import Podcast


class PublishedPodcast(models.Model):
    publisher = models.ForeignKey(settings.AUTH_USER_MODEL)
    podcast = models.ForeignKey(Podcast)
