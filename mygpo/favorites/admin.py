

from django.contrib import admin

from mygpo.favorites.models import FavoriteEpisode


@admin.register(FavoriteEpisode)
class FavoriteEpisodeAdmin(admin.ModelAdmin):
    """ Admin page for favorite episodes """

    # configuration for the list view
    list_display = ('user', 'episode')

    # fetch the related objects for the fields in list_display
    list_select_related = ('user', 'episode')

    raw_id_fields = ('user', 'episode')

    show_full_result_count = False
