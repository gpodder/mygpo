from django.contrib import admin

from mygpo.podcastlists.models import PodcastList, PodcastListEntry
from mygpo.votes.admin import VoteInline


class PodcastListEntryInline(admin.TabularInline):
    model = PodcastListEntry


@admin.register(PodcastList)
class PodcastListAdmin(admin.ModelAdmin):
    """ Admin page for podcast lists"""

    # configuration for the list view
    list_display = ('title', 'user', 'slug', 'num_entries', 'vote_count')

    # fetch related objects for the list view
    list_select_related = ('user',)

    search_fields = ('title', 'user__username', 'slug')

    inlines = [PodcastListEntryInline, VoteInline]

    raw_id_fields = ('user',)

    show_full_result_count = False
