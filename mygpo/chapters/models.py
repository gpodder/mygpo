from django.db import models
from django.conf import settings

from mygpo.core.models import UpdateInfoModel
from mygpo.podcasts.models import Episode, Podcast


class Chapter(UpdateInfoModel):
    """A chapter of an Episode"""

    # Seconds at which the chapter starts and ends
    start = models.IntegerField()
    end = models.IntegerField()

    # name or label of the chapter
    label = models.CharField(max_length=100)

    # indicates if the chapter is an advertisement
    advertisement = models.BooleanField(default=False)

    # the user that created the chapter
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    # the episode to which the chapter belongs
    episode = models.ForeignKey(Episode, on_delete=models.CASCADE)

    class Meta:
        index_together = [
            ("user", "episode", "created"),
            ("episode", "user", "start", "end"),
        ]
