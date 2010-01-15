#
# This file is part of my.gpodder.org.
#
# my.gpodder.org is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# my.gpodder.org is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public
# License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with my.gpodder.org. If not, see <http://www.gnu.org/licenses/>.
#

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

class SubscriptionAdmin(admin.ModelAdmin):
    #empty ModelAdmin to work around bug 685
    pass

class SubscriptionActionAdmin(admin.ModelAdmin):
    #empty ModelAdmin to work around bug 685
    pass

admin.site.unregister(User)
admin.site.register(User, UserProfileAdmin)
admin.site.register(Podcast, PodcastAdmin)
admin.site.register(SyncGroup, SyncGroupAdmin)
admin.site.register(Device, DeviceAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(SubscriptionAction, SubscriptionActionAdmin)
admin.site.register(URLSanitizingRule)

