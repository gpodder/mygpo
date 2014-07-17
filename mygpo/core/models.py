""" This module contains abstract models that are used in multiple apps """

from django.db import models


class TwitterModel(models.Model):
    """ A model that has a twitter handle """

    twitter = models.CharField(max_length=15, null=True, blank=False)

    class Meta:
        abstract = True
