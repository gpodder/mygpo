from django.conf.urls import *

from mygpo.api.subscriptions import SubscriptionsAPI
from mygpo.api.advanced.updates import DeviceUpdates
from mygpo.api.advanced.episode import ChaptersAPI
from mygpo.api.advanced.settings import SettingsAPI

urlpatterns = patterns('mygpo.api.advanced',
 url(r'^api/(?P<version>[12])/subscriptions/(?P<username>[\w.+-]+)/(?P<device_uid>[\w.-]+)\.json',
     SubscriptionsAPI.as_view(), name='subscriptions-api'),

 url(r'^api/(?P<version>[12])/episodes/(?P<username>[\w.+-]+)\.json', 'episodes'),
    (r'^api/[12]/devices/(?P<username>[\w.+-]+)/(?P<device_uid>[\w.-]+)\.json', 'device'),
    (r'^api/[12]/devices/(?P<username>[\w.+-]+)\.json', 'devices'),

    (r'^api/2/auth/(?P<username>[\w.+-]+)/login\.json', 'auth.login'),
    (r'^api/2/auth/(?P<username>[\w.+-]+)/logout\.json', 'auth.logout'),
    (r'^api/2/tags/(?P<count>\d+)\.json', 'directory.top_tags'),
    (r'^api/2/tag/(?P<tag>[^/]+)/(?P<count>\d+)\.json', 'directory.tag_podcasts'),
    (r'^api/2/data/podcast\.json', 'directory.podcast_info'),
 url(r'^api/2/data/episode\.json', 'directory.episode_info', name='api-episode-info'),

    (r'^api/2/chapters/(?P<username>[\w.+-]+)\.json', ChaptersAPI.as_view()),
    (r'^api/2/updates/(?P<username>[\w.+-]+)/(?P<device_uid>[\w.-]+)\.json',
        DeviceUpdates.as_view()),

 url(r'^api/2/settings/(?P<username>[\w.+-]+)/(?P<scope>account|device|podcast|episode)\.json',
        SettingsAPI.as_view(),
        name='settings-api'),

    (r'^api/2/favorites/(?P<username>[\w.+-]+).json', 'favorites'),

    (r'^api/2/lists/(?P<username>[\w.+-]+)/create\.(?P<format>\w+)', 'lists.create'),
    (r'^api/2/lists/(?P<username>[\w.+-]+)\.json',                   'lists.get_lists'),
 url(r'^api/2/lists/(?P<username>[\w.+-]+)/list/(?P<slug>[\w-]+)\.(?P<format>\w+)', 'lists.podcast_list', name='api-get-list'),

    (r'^api/2/sync-devices/(?P<username>[\w.+-]+)\.json', 'sync.main'),
)
