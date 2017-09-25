

from django.contrib import admin

from mygpo.episodestates.models import EpisodeState


@admin.register(EpisodeState)
class EpisodeStateAdmin(admin.ModelAdmin):
    """ Admin page for subscriptions """

    # configuration for the list view
    list_display = ('user', 'episode', 'action')

    # fetch the related objects for the fields in list_display
    list_select_related = ('user', 'episode', )

    raw_id_fields = ('user', 'episode', )

    show_full_result_count = False
