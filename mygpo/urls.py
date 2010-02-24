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


import os.path
from django.conf.urls.defaults import *
from registration.views import activate, register
from registration.forms import RegistrationFormUniqueEmail
from mygpo.api.models import UserProfile
from django.contrib.auth.views import logout


# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^mygpo/', include('mygpo.foo.urls')),
    (r'^$', 'mygpo.web.views.home'),
    (r'^login/$', 'mygpo.web.users.login_user'),
    (r'^logout/$', logout, {'next_page': '/'}),
    (r'^migrate/$', 'mygpo.web.users.migrate_user'),
    (r'^register/resend-activation$', 'mygpo.web.views.resend_activation'),
    (r'^register/restore_password$', 'mygpo.web.users.restore_password'),
    (r'^register/$',  register, {'profile_callback': UserProfile.objects.create, 'success_url': '../registration_complete/', 'form_class': RegistrationFormUniqueEmail}),
    (r'^registration_complete/$', 'django.views.generic.simple.direct_to_template', {'template': 'registration/registration_complete.html'}),
    (r'^activate/(?P<activation_key>\w+)$', activate),

    (r'^podcast/(?P<pid>\w+)$', 'mygpo.web.views.podcast'),
    (r'^podcast/(?P<pid>\w+)/subscribe$', 'mygpo.web.views.podcast_subscribe'),
    (r'^podcast/(?P<pid>\w+)/unsubscribe/(?P<device_id>\d+)', 'mygpo.web.views.podcast_unsubscribe'),

    (r'^episode/(?P<id>\d+)$', 'mygpo.web.views.episode'),

    (r'account/$', 'mygpo.web.views.account'),
    (r'account/delete$', 'mygpo.web.views.delete_account'),

    (r'user/(?P<username>\w+)/subscriptions$', 'mygpo.web.views.user_subscriptions'),

    (r'^history/$', 'mygpo.web.views.history'),
    (r'^devices/$', 'mygpo.web.views.devices'),

    (r'^toplist/$', 'mygpo.web.views.toplist'),
    (r'^toplist/episodes$', 'mygpo.web.views.episode_toplist'),
    (r'^toplist.opml$', 'mygpo.web.views.toplist_opml', {'count': 50}),

    (r'^suggestions/$', 'mygpo.web.views.suggestions'),

    (r'^device/(?P<device_id>\d+)$', 'mygpo.web.views.device'),
    (r'^device/(?P<device_id>\d+)/sync$', 'mygpo.web.views.device_sync'),
    (r'^device/(?P<device_id>\d+)/unsync$', 'mygpo.web.views.device_unsync'),
    (r'^device/(?P<device_id>\d+)/delete$', 'mygpo.web.views.device_delete'),
    (r'^device/(?P<device_id>\d+)/history$', 'mygpo.web.views.history'),

    (r'^search/', include('haystack.urls')),

    #Legacy API
    (r'^upload$', 'mygpo.api.legacy.upload'),
    (r'^getlist$', 'mygpo.api.legacy.getlist'),

    #Simple API
    (r'^subscriptions/(?P<username>\w+)/(?P<device_uid>[\w-\.]+).(?P<format>\w+)', 'mygpo.api.simple.subscriptions'),
    (r'^toplist/(?P<count>\d+).(?P<format>\w+)', 'mygpo.api.simple.toplist'),
    (r'^search.(?P<format>\w+)', 'mygpo.api.simple.search'),
    (r'^suggestions/(?P<count>\d+).(?P<format>\w+)', 'mygpo.api.simple.suggestions'),

    #Advanced API
    (r'^api/1/subscriptions/(?P<username>\w+)/(?P<device_uid>[\w-\.]+).json', 'mygpo.api.advanced.subscriptions'),
    (r'^api/1/episodes/(?P<username>\w+).json', 'mygpo.api.advanced.episodes'),
    (r'^api/1/devices/(?P<username>\w+)/(?P<device_uid>[\w-\.]+).json', 'mygpo.api.advanced.device'),
    (r'^api/1/devices/(?P<username>\w+).json', 'mygpo.api.advanced.devices'),

    #Subscribe with my.gpodder.org
    (r'^subscribe', 'mygpo.web.views.podcast_subscribe_url'),
    #(r'^authors/$', 'django.views.generic.simple.direct_to_template', {'template': 'authors.html'}),
    (r'^authors/$', 'mygpo.web.views.author'),


    (r'^online-help', 'django.views.generic.simple.direct_to_template', {'template': 'online-help.html'}),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/(.*)', admin.site.root),

    (r'^accounts/', include('registration.urls')),

    (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': os.path.abspath('%s/../htdocs/media/' % os.path.dirname(__file__))}),

)

