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
from django.contrib.auth.views import logout


# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^mygpo/', include('mygpo.foo.urls')),
    (r'^$', 'mygpo.web.views.home'),
    (r'^media/logo/(?P<size>\d+)/(?P<filename>[^/]*)\.jpg$', 'mygpo.web.views.cover_art'),
    (r'^logo/(?P<size>\d+)/(?P<filename>[^/]*)\.jpg$', 'mygpo.web.views.cover_art'),
    (r'^subscriptions/$', 'mygpo.web.views.subscriptions'),
    (r'^download/subscriptions\.opml$', 'mygpo.web.views.all_subscriptions_download'),
    (r'^subscriptions/all.opml$', 'mygpo.web.views.all_subscriptions_download'),
    (r'^login/$', 'mygpo.web.users.login_user'),
    (r'^logout/$', logout, {'next_page': '/'}),
    (r'^migrate/$', 'mygpo.web.users.migrate_user'),
    (r'^register/resend-activation$', 'mygpo.web.views.resend_activation'),
    (r'^register/restore_password$', 'mygpo.web.users.restore_password'),
    (r'^register/$',  register, {'backend': 'registration.backends.default.DefaultBackend', 'form_class': RegistrationFormUniqueEmail}),
    (r'^registration_complete/$', 'django.views.generic.simple.direct_to_template', {'template': 'registration/registration_complete.html'}),
    (r'^activate/(?P<activation_key>\w+)$', activate, {'backend': 'registration.backends.default.DefaultBackend'}),

    (r'^podcast/(?P<pid>\w+)$', 'mygpo.web.views.podcast.show'),
    (r'^podcast/(?P<pid>\w+)/subscribe$', 'mygpo.web.views.podcast_subscribe'),
    (r'^podcast/(?P<pid>\w+)/unsubscribe/(?P<device_id>\d+)', 'mygpo.web.views.podcast_unsubscribe'),
    (r'^podcast/(?P<pid>\w+)/add-tag', 'mygpo.web.views.podcast.add_tag'),
    (r'^podcast/(?P<pid>\w+)/remove-tag', 'mygpo.web.views.podcast.remove_tag'),

    (r'^episode/(?P<id>\d+)$', 'mygpo.web.views.episode.episode'),
    (r'^episode/(?P<id>\d+)/add-chapter$', 'mygpo.web.views.episode.add_chapter'),
    (r'^episode/(?P<id>\d+)/remove-chapter/(?P<chapter_id>\d+)$', 'mygpo.web.views.episode.remove_chapter'),
    (r'^episode/(?P<id>\d+)/toggle-favorite', 'mygpo.web.views.episode.toggle_favorite'),

    (r'^favorites/', 'mygpo.web.views.episode.list_favorites'),

    (r'account/$', 'mygpo.web.views.settings.account'),
    (r'account/privacy$', 'mygpo.web.views.settings.privacy'),
    (r'account/delete$', 'mygpo.web.views.settings.delete_account'),
    (r'share/$', 'mygpo.web.views.settings.share'),

    (r'user/(?P<username>\w+)/subscriptions$', 'mygpo.web.views.user_subscriptions'),
    (r'user/(?P<username>\w+)/subscriptions\.opml$', 'mygpo.web.views.user_subscriptions_opml'),
    (r'user/(?P<username>\w+)/favorites.xml$', 'mygpo.userfeeds.views.favorite_feed'),

    (r'^history/$', 'mygpo.web.views.history'),

    (r'^directory/$', 'mygpo.web.views.public.browse'),
    (r'^directory/(?P<category>[^/]+)$', 'mygpo.web.views.public.category'),

    (r'^toplist/$', 'mygpo.web.views.toplist'),
    (r'^toplist/episodes$', 'mygpo.web.views.episode_toplist'),
    (r'^toplist.opml$', 'mygpo.api.simple.toplist', {'count': 50, 'format': 'opml'}),

    (r'^gpodder-examples.opml$', 'mygpo.web.views.gpodder_example_podcasts'),

    (r'^suggestions/$', 'mygpo.web.views.suggestions'),

    (r'^devices/$', 'mygpo.web.views.device.overview'),
    (r'^device/(?P<device_id>\d+)$', 'mygpo.web.views.device.show'),
    (r'^device/(?P<device_id>\d+).opml$', 'mygpo.web.views.device.opml'),
    (r'^device/(?P<device_id>\d+)/sync$', 'mygpo.web.views.device.sync'),
    (r'^device/(?P<device_id>\d+)/unsync$', 'mygpo.web.views.device.unsync'),
    (r'^device/(?P<device_id>\d+)/delete$', 'mygpo.web.views.device.delete'),
    (r'^device/(?P<device_id>\d+)/remove$', 'mygpo.web.views.device.delete_permanently'),
    (r'^device/(?P<device_id>\d+)/undelete$', 'mygpo.web.views.device.undelete'),
    (r'^device/(?P<device_id>\d+)/history$', 'mygpo.web.views.history'),
    (r'^device/(?P<device_id>\d+)/edit$', 'mygpo.web.views.device.edit'),

    (r'^search/', 'mygpo.search.views.search'),

    (r'^tags/', 'mygpo.web.views.mytags'),

    #Legacy API
    (r'^upload$', 'mygpo.api.legacy.upload'),
    (r'^getlist$', 'mygpo.api.legacy.getlist'),

    #Simple API
    (r'^subscriptions/(?P<username>\w+)/(?P<device_uid>[\w.-]+)\.(?P<format>\w+)', 'mygpo.api.simple.subscriptions'),
    (r'^subscriptions/(?P<username>\w+)\.(?P<format>\w+)', 'mygpo.api.simple.all_subscriptions'),
    (r'^toplist/(?P<count>\d+)\.(?P<format>\w+)', 'mygpo.api.simple.toplist'),
    (r'^search\.(?P<format>\w+)', 'mygpo.api.simple.search'),
    (r'^suggestions/(?P<count>\d+)\.(?P<format>\w+)', 'mygpo.api.simple.suggestions'),

    #Advanced API
    (r'^api/[12]/subscriptions/(?P<username>\w+)/(?P<device_uid>[\w.-]+)\.json', 'mygpo.api.advanced.subscriptions'),
    (r'^api/(?P<version>[12])/episodes/(?P<username>\w+)\.json', 'mygpo.api.advanced.episodes'),
    (r'^api/[12]/devices/(?P<username>\w+)/(?P<device_uid>[\w.-]+)\.json', 'mygpo.api.advanced.device'),
    (r'^api/[12]/devices/(?P<username>\w+)\.json', 'mygpo.api.advanced.devices'),

    (r'^api/2/auth/(?P<username>\w+)/(?P<device_uid>[\w.-]+)/login\.json', 'mygpo.api.advanced.auth.login'),
    (r'^api/2/auth/(?P<username>\w+)/(?P<device_uid>[\w.-]+)/logout\.json', 'mygpo.api.advanced.auth.logout'),
    (r'^api/2/auth/(?P<username>\w+)/(?P<device_uid>[\w.-]+)/validate\.json', 'mygpo.api.advanced.auth.validate'),
    (r'^api/2/tags/(?P<count>\d+)\.json', 'mygpo.api.advanced.directory.top_tags'),
    (r'^api/2/tag/(?P<tag>[^/]+)/(?P<count>\d+)\.json', 'mygpo.api.advanced.directory.tag_podcasts'),
    (r'^api/2/data/podcast\.json', 'mygpo.api.advanced.directory.podcast_info'),
    (r'^api/2/data/episode\.json', 'mygpo.api.advanced.directory.episode_info'),

    (r'^api/2/chapters/(?P<username>\w+)\.json', 'mygpo.api.advanced.episode.chapters'),
    (r'^api/2/updates/(?P<username>\w+)/(?P<device_uid>[\w.-]+)\.json', 'mygpo.api.advanced.updates'),

    (r'^api/2/settings/(?P<username>\w+)/(?P<scope>account|device|podcast|episode)\.json', 'mygpo.api.advanced.settings.main'),
    (r'^api/2/favorites/(?P<username>\w+).json', 'mygpo.api.advanced.favorites'),

    #Subscribe with my.gpodder.org
    (r'^subscribe', 'mygpo.web.views.podcast_subscribe_url'),


    (r'^online-help', 'django.views.generic.simple.direct_to_template', {'template': 'online-help.html'}),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/(.*)', admin.site.root),

    (r'^accounts/', include('registration.urls')),

    (r'^publisher/$', 'mygpo.publisher.views.home'),
    (r'^publisher/(?P<username>\w+)/update', 'mygpo.publisher.views.update_published_podcasts'),
    (r'^publisher/podcast/(?P<id>\d+)$', 'mygpo.publisher.views.podcast'),
    (r'^publisher/podcast/(?P<id>\d+)/update$', 'mygpo.publisher.views.update_podcast'),
    (r'^publisher/podcast/(?P<id>\d+)/episodes$', 'mygpo.publisher.views.episodes'),
    (r'^publisher/episode/(?P<id>\d+)$', 'mygpo.publisher.views.episode'),
    (r'^publisher/podcast/search$', 'mygpo.publisher.views.search_podcast'),
    (r'^publisher/group/(?P<group_id>\d+)$', 'mygpo.publisher.views.group'),

    (r'^publisher/link/$', 'mygpo.publisher.views.link'),
    (r'^publisher/advertise', 'mygpo.publisher.views.advertise'),

    #Subscribe with my.gpodder.org
    (r'^subscribe', 'mygpo.web.views.podcast_subscribe_url'),
    #(r'^authors/$', 'mygpo.web.views.author'),


    (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': os.path.abspath('%s/../htdocs/media/' % os.path.dirname(__file__))}),

)

