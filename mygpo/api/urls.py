from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^upload$', 'mygpo.api.legacy.upload'),
    (r'^getlist$', 'mygpo.api.legacy.getlist'),
    (r'^toplist.opml$', 'mygpo.api.simple.toplist', {'count': 50, 'format': 'opml'}),
)

urlpatterns += patterns('mygpo.api.simple',
    (r'^subscriptions/(?P<username>\w+)/(?P<device_uid>[\w.-]+)\.(?P<format>\w+)', 'subscriptions'),
    (r'^subscriptions/(?P<username>\w+)\.(?P<format>\w+)', 'all_subscriptions'),
    (r'^toplist/(?P<count>\d+)\.(?P<format>\w+)', 'toplist'),
    (r'^search\.(?P<format>\w+)', 'search'),
    (r'^suggestions/(?P<count>\d+)\.(?P<format>\w+)', 'suggestions'),
    (r'^toplist.opml$', 'toplist', {'count': 50, 'format': 'opml'}),
)

urlpatterns += patterns('mygpo.api.advanced',
    (r'^api/[12]/subscriptions/(?P<username>\w+)/(?P<device_uid>[\w.-]+)\.json', 'subscriptions'),
    (r'^api/(?P<version>[12])/episodes/(?P<username>\w+)\.json', 'episodes'),
    (r'^api/[12]/devices/(?P<username>\w+)/(?P<device_uid>[\w.-]+)\.json', 'device'),
    (r'^api/[12]/devices/(?P<username>\w+)\.json', 'devices'),

    (r'^api/2/auth/(?P<username>\w+)/(?P<device_uid>[\w.-]+)/login\.json', 'auth.login'),
    (r'^api/2/auth/(?P<username>\w+)/(?P<device_uid>[\w.-]+)/logout\.json', 'auth.logout'),
    (r'^api/2/auth/(?P<username>\w+)/(?P<device_uid>[\w.-]+)/validate\.json', 'auth.validate'),
    (r'^api/2/tags/(?P<count>\d+)\.json', 'directory.top_tags'),
    (r'^api/2/tag/(?P<tag>[^/]+)/(?P<count>\d+)\.json', 'directory.tag_podcasts'),
    (r'^api/2/data/podcast\.json', 'directory.podcast_info'),
    (r'^api/2/data/episode\.json', 'directory.episode_info'),

    (r'^api/2/chapters/(?P<username>\w+)\.json', 'episode.chapters'),
    (r'^api/2/updates/(?P<username>\w+)/(?P<device_uid>[\w.-]+)\.json', 'updates'),

    (r'^api/2/settings/(?P<username>\w+)/(?P<scope>account|device|podcast|episode)\.json', 'settings.main'),
    (r'^api/2/favorites/(?P<username>\w+).json', 'favorites'),

)
