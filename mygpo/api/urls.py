from django.conf.urls import url

from . import legacy, simple, advanced, advanced, subscriptions
from .advanced import auth, lists, sync, updates, episode, settings


urlpatterns = [
    url(r'^upload$',
        legacy.upload),

    url(r'^getlist$',
        legacy.getlist),

    url(r'^toplist.opml$',
        simple.toplist,
        kwargs={'count': 50, 'format': 'opml'}),

    url(r'^subscriptions/(?P<username>[\w.+-]+)/'
        '(?P<device_uid>[\w.-]+)\.(?P<format>\w+)',
        simple.subscriptions),

    url(r'^subscriptions/(?P<username>[\w.+-]+)\.(?P<format>\w+)',
        simple.all_subscriptions,
        name='api-all-subscriptions'),

    url(r'^toplist/(?P<count>\d+)\.(?P<format>\w+)',
        simple.toplist,
        name='toplist-opml'),

    url(r'^search\.(?P<format>\w+)',
        simple.search),

    url(r'^suggestions/(?P<count>\d+)\.(?P<format>\w+)',
        simple.suggestions,
        name='suggestions-opml'),

    url(r'^toplist\.(?P<format>\w+)$',
        simple.toplist,
        kwargs={'count': 50}),

    url(r'^gpodder-examples\.(?P<format>\w+)$',
        simple.example_podcasts,
        name='example-opml'),

    url(r'^api/(?P<version>[12])/subscriptions/(?P<username>[\w.+-]+)/'
        '(?P<device_uid>[\w.-]+)\.json',
        subscriptions.SubscriptionsAPI.as_view(),
        name='subscriptions-api'),

    url(r'^api/(?P<version>[12])/episodes/(?P<username>[\w.+-]+)\.json',
        advanced.episodes),

    url(r'^api/[12]/devices/(?P<username>[\w.+-]+)/'
        '(?P<device_uid>[\w.-]+)\.json',
        advanced.device),

    url(r'^api/[12]/devices/(?P<username>[\w.+-]+)\.json',
        advanced.devices),

    url(r'^api/2/auth/(?P<username>[\w.+-]+)/login\.json',
        auth.login),

    url(r'^api/2/auth/(?P<username>[\w.+-]+)/logout\.json',
        auth.logout),

    url(r'^api/2/tags/(?P<count>\d+)\.json',
        advanced.directory.top_tags),

    url(r'^api/2/tag/(?P<tag>[^/]+)/(?P<count>\d+)\.json',
        advanced.directory.tag_podcasts),

    url(r'^api/2/data/podcast\.json',
        advanced.directory.podcast_info),

    url(r'^api/2/data/episode\.json',
        advanced.directory.episode_info,
        name='api-episode-info'),

    url(r'^api/2/chapters/(?P<username>[\w.+-]+)\.json',
        episode.ChaptersAPI.as_view()),

    url(r'^api/2/updates/(?P<username>[\w.+-]+)/(?P<device_uid>[\w.-]+)\.json',
        updates.DeviceUpdates.as_view()),

    url(r'^api/2/settings/(?P<username>[\w.+-]+)/'
        '(?P<scope>account|device|podcast|episode)\.json',
        settings.SettingsAPI.as_view(),
        name='settings-api'),

    url(r'^api/2/favorites/(?P<username>[\w.+-]+).json',
        advanced.favorites),

    url(r'^api/2/lists/(?P<username>[\w.+-]+)/create\.(?P<format>\w+)',
        lists.create),

    url(r'^api/2/lists/(?P<username>[\w.+-]+)\.json',
        lists.get_lists),

    url(r'^api/2/lists/(?P<username>[\w.+-]+)/list/'
        '(?P<slug>[\w-]+)\.(?P<format>\w+)',
        lists.podcast_list,
        name='api-get-list'),

    url(r'^api/2/sync-devices/(?P<username>[\w.+-]+)\.json',
        sync.main),

]
