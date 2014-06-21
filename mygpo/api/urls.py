from django.conf.urls import *

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

from mygpo.api.subscriptions import SubscriptionsAPI
from mygpo.api.advanced.updates import DeviceUpdates

urlpatterns += patterns('mygpo.api.advanced',
 url(r'^api/(?P<version>[12])/subscriptions/(?P<username>[\w.-]+)/(?P<device_uid>[\w.-]+)\.json',
     SubscriptionsAPI.as_view(), name='subscriptions-api'),

 url(r'^api/(?P<version>[12])/episodes/(?P<username>[\w.-]+)\.json', 'episodes'),
    (r'^api/[12]/devices/(?P<username>[\w.-]+)/(?P<device_uid>[\w.-]+)\.json', 'device'),
    (r'^api/[12]/devices/(?P<username>[\w.-]+)\.json', 'devices'),

    (r'^api/2/auth/(?P<username>[\w.-]+)/login\.json', 'auth.login'),
    (r'^api/2/auth/(?P<username>[\w.-]+)/logout\.json', 'auth.logout'),
    (r'^api/2/tags/(?P<count>\d+)\.json', 'directory.top_tags'),
    (r'^api/2/tag/(?P<tag>[^/]+)/(?P<count>\d+)\.json', 'directory.tag_podcasts'),
    (r'^api/2/data/podcast\.json', 'directory.podcast_info'),
 url(r'^api/2/data/episode\.json', 'directory.episode_info', name='api-episode-info'),

    (r'^api/2/chapters/(?P<username>[\w.-]+)\.json', 'episode.chapters'),
    (r'^api/2/updates/(?P<username>[\w.-]+)/(?P<device_uid>[\w.-]+)\.json',
        DeviceUpdates.as_view()),

    (r'^api/2/settings/(?P<username>[\w.-]+)/(?P<scope>account|device|podcast|episode)\.json', 'settings.main'),
    (r'^api/2/favorites/(?P<username>[\w.-]+).json', 'favorites'),

    (r'^api/2/lists/(?P<username>[\w.-]+)/create\.(?P<format>\w+)', 'lists.create'),
    (r'^api/2/lists/(?P<username>[\w.-]+)\.json',                   'lists.get_lists'),
 url(r'^api/2/lists/(?P<username>[\w.-]+)/list/(?P<listname>[\w-]+)\.(?P<format>\w+)', 'lists.podcast_list', name='api-get-list'),

    (r'^api/2/sync-devices/(?P<username>\w+)\.json', 'sync.main'),
)
