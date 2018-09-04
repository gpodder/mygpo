from datetime import datetime

from django.db import models
from django.contrib.postgres.fields import ArrayField


class AuthRequest(models.Model):

    scopes = ArrayField(models.CharField(max_length=64, blank=True))

    state = models.CharField(max_length=32)

    created = models.DateTimeField(default=datetime.utcnow)
