from django.contrib import admin
from mygpo.api.models import *

class DeviceInline(admin.TabularInline):
    model = Device
    extra = 3

class EpisodeInline(admin.TabularInline):
    model = Episode
    extra = 3

class EpisodeActionInline(admin.TabularInline):
    model = EpisodeAction
    extra = 3

class SubscriptionActionInline(admin.TabularInline):
    model = SubscriptionAction
    extra = 3

class UserAdmin(admin.ModelAdmin):
    inlines = [DeviceInline, EpisodeActionInline]

class PodcastAdmin(admin.ModelAdmin):
    inlines = [EpisodeInline]

class DeviceAdmin(admin.ModelAdmin):
    inlines = [SubscriptionActionInline]

admin.site.register(User, UserAdmin)
admin.site.register(Podcast, PodcastAdmin)
admin.site.register(Device, DeviceAdmin)
admin.site.register(Subscription)

