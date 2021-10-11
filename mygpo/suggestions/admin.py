from django.contrib import admin

from mygpo.suggestions.models import PodcastSuggestion


@admin.register(PodcastSuggestion)
class PodcastSuggestionAdmin(admin.ModelAdmin):
    """Admin page for suggestions"""

    # configuration for the list view
    list_display = ("suggested_to", "podcast", "deleted")

    # fetch the related objects for the fields in list_display
    list_select_related = ("suggested_to", "podcast")

    raw_id_fields = ("suggested_to", "podcast")

    show_full_result_count = False
