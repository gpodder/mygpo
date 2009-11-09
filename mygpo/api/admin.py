from django.contrib import admin
from django import forms
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

class UserAccountForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(UserAccountForm, self).__init__(*args, **kwargs)
        self.fields['default_device'].queryset = Device.objects.filter(user=self.instance)

class UserAccountAdmin(admin.ModelAdmin):
    inlines = [DeviceInline, EpisodeActionInline]
    form = UserAccountForm

class PodcastAdmin(admin.ModelAdmin):
    inlines = [EpisodeInline]
    list_display = ['title', 'description', 'url', 'link', 'last_update', 'subscription_count']

class DeviceAdmin(admin.ModelAdmin):
    inlines = [SubscriptionActionInline]

admin.site.register(UserAccount, UserAccountAdmin)
admin.site.register(Podcast, PodcastAdmin)
admin.site.register(Device, DeviceAdmin)
admin.site.register(Subscription)
admin.site.register(SubscriptionAction)
