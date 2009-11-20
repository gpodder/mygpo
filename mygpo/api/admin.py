from django.contrib import admin
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
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

class SyncGroupAdmin(admin.ModelAdmin):
    inlines = [DeviceInline]

class UserProfileInline(admin.StackedInline):
    model = UserProfile

class UserProfileAdmin(admin.ModelAdmin):
    inlines = [UserProfileInline, DeviceInline, EpisodeActionInline]

class PodcastAdmin(admin.ModelAdmin):
    inlines = [EpisodeInline]
    list_display = ['title', 'description', 'url', 'link', 'last_update', 'subscription_count']

class DeviceAdmin(admin.ModelAdmin):
    inlines = [SubscriptionActionInline]

admin.site.unregister(User)
admin.site.register(User, UserProfileAdmin)
admin.site.register(Podcast, PodcastAdmin)
admin.site.register(SyncGroup, SyncGroupAdmin)
admin.site.register(Device, DeviceAdmin)
admin.site.register(Subscription)
admin.site.register(SubscriptionAction)

