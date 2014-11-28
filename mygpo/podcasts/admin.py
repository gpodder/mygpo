from __future__ import unicode_literals

from django.utils.html import format_html
from django.utils.translation import ugettext as _
from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from mygpo.podcasts.models import (Podcast, Episode, URL, Slug, Tag,
    MergedUUID, PodcastGroup)
from mygpo.utils import edit_link


class AdminLinkMixin(object):
    """ Adds an Admin link """

    def admin_link(self, instance):
        """ Link to the admin page """

        if not instance.pk:
            return ''

        url = edit_link(instance)
        return format_html('<a href="{}">{}</a>', url, _('Edit'))

    readonly_fields = ('admin_link',)


class AdminLinkInline(AdminLinkMixin, admin.TabularInline):
    """ TabularInline that adds an Admin link for the inlined model """


class GenericAdminLinkInline(AdminLinkMixin, GenericTabularInline):
    """ TabularInline that adds an Admin link for the inlined model """


@admin.register(URL)
class URLAdmin(admin.ModelAdmin):
    model = URL
    list_display = ('url', 'content_type', 'object_id')
    list_filter = ('content_type', )


class URLInline(GenericAdminLinkInline):
    model = URL
    fields = ('order', 'url', 'admin_link', )


class SlugInline(GenericTabularInline):
    model = Slug


class TagInline(GenericTabularInline):
    model = Tag


class MergedUUIDInline(GenericTabularInline):
    model = MergedUUID


class PodcastInline(AdminLinkInline):
    model = Podcast

    fields = ('id', 'title', 'group_member_name', 'admin_link')

    readonly_fields = ('id', ) + AdminLinkInline.readonly_fields

    can_delete = False

    def has_add_permission(self, request):
        """ Podcasts must be created and then added to the group """
        return False


@admin.register(Podcast)
class PodcastAdmin(admin.ModelAdmin):
    """ Admin page for podcasts """

    # configuration for the list view
    list_display = ('title', 'main_url', )

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
                       'content_types', 'max_episode_order', )
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

    list_filter = ('language', )
    search_fields = ('title', '^urls__url')

    # configuration for the create / edit view
    fieldsets = (
        (None, {
            'fields': ('id', 'title', 'subtitle', 'description', 'link',
                       'language', 'guid', 'released', 'podcast', 'order', )
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


@admin.register(PodcastGroup)
class PodcastGroupAdmin(admin.ModelAdmin):
    """ Admin page for podcast groups """

    # configuration for the list view
    list_display = ('title', )

    search_fields = ('title', )

    inlines = [
        PodcastInline,
    ]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """ Admin page for tags """

    list_display = ('tag', 'content_object', 'source', 'user', )

    list_filter = ('source', )
