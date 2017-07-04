from django.contrib import admin

from mygpo.usersettings.models import UserSettings


@admin.register(UserSettings)
class PodcastConfigAdmin(admin.ModelAdmin):

    # configuration for the list view
    list_display = ('user', 'content_object', )

    # fetch the related objects for the fields in list_display
    list_select_related = ('user', 'content_object', )

    raw_id_fields = ('user', )
