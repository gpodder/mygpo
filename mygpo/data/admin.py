from django.contrib import admin

from . import models


@admin.register(models.PodcastUpdateResult)
class PodcastUpdateResultAdmin(admin.ModelAdmin):
    model = models.PodcastUpdateResult

    list_display = ['title', 'start', 'duration', 'successful',
                    'episodes_added']

    readonly_fields = ['id', 'podcast_url', 'podcast', 'start', 'duration',
                       'successful', 'error_message', 'podcast_created',
                       'episodes_added']

    def title(self, res):
        return res.podcast or res.podcast_url
