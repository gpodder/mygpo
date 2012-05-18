from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^upload$', 'mygpo.api.legacy.upload'),
    (r'^getlist$', 'mygpo.api.legacy.getlist'),
    (r'^toplist.opml$', 'mygpo.api.simple.toplist', {'count': 50, 'format': 'opml'}),
)

urlpatterns += patterns('mygpo.api.simple',
    (r'^subscriptions/(?P<username>[\w.-]+)/(?P<device_uid>[\w.-]+)\.(?P<format>\w+)', 'subscriptions'),
    (r'^subscriptions/(?P<username>[\w.-]+)\.(?P<format>\w+)', 'all_subscriptions'),
 url(r'^toplist/(?P<count>\d+)\.(?P<format>\w+)', 'toplist',                   name='toplist-opml'),
    (r'^search\.(?P<format>\w+)', 'search'),
 url(r'^suggestions/(?P<count>\d+)\.(?P<format>\w+)', 'suggestions',           name='suggestions-opml'),
    (r'^toplist\.(?P<format>\w+)$', 'toplist', {'count': 50}),
 url(r'^gpodder-examples\.(?P<format>\w+)$', 'example_podcasts',               name='example-opml'),
)

from mygpo.api.advanced.subscriptions import SubscriptionEndpoint
from mygpo.api.advanced.episode import EpisodeActionEndpoint, ChaptersEndpoint, \
         FavoritesEndpoint
from mygpo.api.advanced.devices import DeviceEndpoint, DeviceListEndpoint, \
         DeviceUpdateEndpoint
from mygpo.api.advanced.directory import TopTagsEndpoint, TopPodcastsEndpoint, \
         PodcastInfoEndpoint, EpisodeInfoEndpoint
from mygpo.api.advanced.settings import SettingsEndpoint
from mygpo.api.advanced.lists import CreatePodcastListEndpoint, \
         UserPodcastListsEndpoint, PodcastListEndpoint
from mygpo.api.advanced.sync import SynchronizeEndpoint
from mygpo.api.advanced.auth import LoginEndpoint, LogoutEndpoint

urlpatterns += patterns('',
    (r'^api/[12]/subscriptions/(?P<username>[\w.-]+)/(?P<device_uid>[\w.-]+)\.json', SubscriptionEndpoint.as_view()),
    (r'^api/(?P<version>[12])/episodes/(?P<username>[\w.-]+)\.json', EpisodeActionEndpoint.as_view()),
    (r'^api/[12]/devices/(?P<username>[\w.-]+)/(?P<device_uid>[\w.-]+)\.json', DeviceEndpoint.as_view()),
    (r'^api/[12]/devices/(?P<username>[\w.-]+)\.json', DeviceListEndpoint.as_view()),

    (r'^api/2/auth/(?P<username>[\w.-]+)/login\.json', LoginEndpoint.as_view()),
    (r'^api/2/auth/(?P<username>[\w.-]+)/logout\.json', LogoutEndpoint.as_view()),
    (r'^api/2/tags/(?P<count>\d+)\.json', TopTagsEndpoint.as_view()),
    (r'^api/2/tag/(?P<tag>[^/]+)/(?P<count>\d+)\.json', TopPodcastsEndpoint.as_view()),
    (r'^api/2/data/podcast\.json', PodcastInfoEndpoint.as_view()),
    (r'^api/2/data/episode\.json', EpisodeInfoEndpoint.as_view()),

    (r'^api/2/chapters/(?P<username>[\w.-]+)\.json', ChaptersEndpoint.as_view()),
    (r'^api/2/updates/(?P<username>[\w.-]+)/(?P<device_uid>[\w.-]+)\.json', DeviceUpdateEndpoint.as_view()),

    (r'^api/2/settings/(?P<username>[\w.-]+)/(?P<scope>account|device|podcast|episode)\.json', SettingsEndpoint.as_view()),
    (r'^api/2/favorites/(?P<username>[\w.-]+).json', FavoritesEndpoint.as_view()),

    (r'^api/2/lists/(?P<username>[\w.-]+)/create\.(?P<format>\w+)', CreatePodcastListEndpoint.as_view()),
    (r'^api/2/lists/(?P<username>[\w.-]+)\.json',                   UserPodcastListsEndpoint.as_view()),
 url(r'^api/2/lists/(?P<username>[\w.-]+)/list/(?P<listname>[\w-]+)\.(?P<format>\w+)', PodcastListEndpoint.as_view(), name='api-get-list'),

    (r'^api/2/sync-devices/(?P<username>\w+)\.json', SynchronizeEndpoint.as_view()),
)
