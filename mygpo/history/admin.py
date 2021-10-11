from django.contrib import admin

from mygpo.history.models import HistoryEntry, EpisodeHistoryEntry


@admin.register(HistoryEntry)
class HistoryEntryAdmin(admin.ModelAdmin):
    """Admin page for history entries"""

    # configuration for the list view
    list_display = ("user", "timestamp", "podcast", "action", "client")

    # fetch the related objects for the fields in list_display
    list_select_related = ("user", "podcast", "client")

    raw_id_fields = ("user", "podcast", "client")

    show_full_result_count = False


@admin.register(EpisodeHistoryEntry)
class EpisodeHistoryEntryAdmin(admin.ModelAdmin):
    """Admin page for episode history entries"""

    # configuration for the list view
    list_display = ("user", "timestamp", "episode", "action", "client")

    # fetch the related objects for the fields in list_display
    list_select_related = ("user", "episode", "client")

    raw_id_fields = ("user", "episode", "client")

    show_full_result_count = False
