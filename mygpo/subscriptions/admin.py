from __future__ import unicode_literals

from django.contrib import admin

from mygpo.subscriptions.models import Subscription, PodcastConfig


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """ Admin page for subscriptions """

    # configuration for the list view
    list_display = ('user', 'podcast', 'client', )

    # fetch the related objects for the fields in list_display
    list_select_related = ('user', 'podcast', 'client', )

    raw_id_fields = ('user', 'podcast', 'client', )


@admin.register(PodcastConfig)
class PodcastConfigAdmin(admin.ModelAdmin):

    # configuration for the list view
    list_display = ('user', 'podcast', )

    # fetch the related objects for the fields in list_display
    list_select_related = ('user', 'podcast', )

    raw_id_fields = ('user', 'podcast', )
