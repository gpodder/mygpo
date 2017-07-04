

from django.contrib import admin

from mygpo.pubsub.models import HubSubscription


@admin.register(HubSubscription)
class HubSubscriptionAdmin(admin.ModelAdmin):
    """ Admin page for pubsubhubbub subscriptions """

    # configuration for the list view
    list_display = ('podcast', 'hub_url', 'mode', 'verified')

    # fetch the related objects for the fields in list_display
    list_select_related = ('podcast', )

    raw_id_fields = ('podcast', )

    list_filter = ('mode', 'verified', )

    search_fields = ('topic_url', 'podcast__title', 'hub_url', )
