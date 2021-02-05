from django.contrib import admin

from mygpo.publisher.models import PublishedPodcast


@admin.register(PublishedPodcast)
class ClientAdmin(admin.ModelAdmin):
    """ Admin page for published podcasts"""

    # configuration for the list view
    list_display = ("publisher", "podcast")

    # fetch the related fields for the list_display
    list_select_related = ("publisher", "podcast")

    raw_id_fields = ("publisher", "podcast")

    show_full_result_count = False
