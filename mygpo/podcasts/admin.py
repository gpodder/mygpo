from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from mygpo.podcasts.models import Podcast, Episode, URL, Slug, Tag, MergedUUID


@admin.register(URL)
class URLAdmin(admin.ModelAdmin):
    model = URL
    list_display = ('url', 'content_type', 'object_id')
    list_filter = ('content_type', )


class URLInline(GenericTabularInline):
    model = URL


class SlugInline(GenericTabularInline):
    model = Slug


class TagInline(GenericTabularInline):
    model = Tag


class MergedUUIDInline(GenericTabularInline):
    model = MergedUUID


@admin.register(Podcast)
class PodcastAdmin(admin.ModelAdmin):
    """ Admin page for podcasts """

    # configuration for the list view
    list_display = ('title', 'main_url', )

    # fetch the podcast's URL for the fields in list_display
    list_select_related = ('urls', )

    list_filter = ('language', )
    search_fields = ('title', 'twitter', '^urls__url', )

    # configuration for the create / edit view
    fieldsets = (
        (None, {
            'fields': ('id', 'title', 'subtitle', 'description', 'link',
                       'language')
        }),
        ('Additional information', {
            'fields': ('created', 'license', 'flattr_url', 'author', 'twitter',
                       'related_podcasts', )
        }),
        ('Podcast Group', {
            'fields': ('group', 'group_member_name',)
        }),
        ('Episodes', {
            'fields': ('common_episode_title', 'latest_episode_timestamp',
                       'content_types', )
        }),
        ('Feed updates', {
            'fields': ('outdated', 'new_location', 'last_update', )
        }),
        ('Admin', {
            'fields': ('restrictions', 'hub', )
        }),
    )

    inlines = [
        URLInline,
        SlugInline,
        TagInline,
        MergedUUIDInline,
    ]

    raw_id_fields = ('related_podcasts', )

    readonly_fields = ('id', 'created', 'last_update', )

    def main_url(self, podcast):
        url = podcast.urls.first()
        if url is None:
            return ''

        return url.url


@admin.register(Episode)
class EpisodeAdmin(admin.ModelAdmin):
    """ Admin page for episodes """

    # configuration for the list view
    list_display = ('title', 'podcast_title', 'main_url', )

    # fetch the episode's podcast and URL for the fields in list_display
    list_select_related = ('podcast', 'urls', )

    list_filter = ('language', )
    search_fields = ('title', '^urls__url')

    # configuration for the create / edit view
    fieldsets = (
        (None, {
            'fields': ('id', 'title', 'subtitle', 'description', 'link',
                       'language', 'guid', 'released', 'podcast', )
        }),
        ('Additional information', {
            'fields': ('created', 'license', 'flattr_url', 'author', 'content',
                       'listeners', )
        }),
        ('Media file', {
            'fields': ('duration', 'filesize', 'content_types', 'mimetypes', )
        }),
        ('Feed updates', {
            'fields': ('outdated', 'last_update', )
        }),
    )

    inlines = [
        URLInline,
        SlugInline,
        MergedUUIDInline,
    ]

    raw_id_fields = ('podcast', )

    readonly_fields = ('id', 'created', 'last_update', )

    def podcast_title(self, episode):
        return episode.podcast.title

    def main_url(self, episode):
        return episode.urls.first().url
