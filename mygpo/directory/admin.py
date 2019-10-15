from django.contrib import admin

from mygpo.directory.models import ExamplePodcast


@admin.register(ExamplePodcast)
class ExamplePodcastAdmin(admin.ModelAdmin):
    """ Admin page for example podcasts """

    # configuration for the list view
    list_display = ('podcast',)

    # fetch the related objects for the fields in list_display
    list_select_related = ('podcast',)

    raw_id_fields = ('podcast',)
