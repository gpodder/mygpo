from django.contrib import admin

from mygpo.subscriptions.models import Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """ Admin page for subscriptions """

    # configuration for the list view
    list_display = ('user', 'podcast', 'client')

    # fetch the related objects for the fields in list_display
    list_select_related = ('user', 'podcast', 'client')

    raw_id_fields = ('user', 'podcast', 'client')

    show_full_result_count = False
