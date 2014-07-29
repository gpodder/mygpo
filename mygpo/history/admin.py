from __future__ import unicode_literals

from django.contrib import admin

from mygpo.history.models import HistoryEntry


@admin.register(HistoryEntry)
class HistoryEntryAdmin(admin.ModelAdmin):
    """ Admin page for history entries """

    # configuration for the list view
    list_display = ('user', 'timestamp', 'podcast', 'action', 'client', )

    # fetch the related objects for the fields in list_display
    list_select_related = ('user', 'podcast', 'client', )

    raw_id_fields = ('user', 'podcast', 'client', )
