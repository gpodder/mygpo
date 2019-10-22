from django.urls import path, register_converter

from . import legacy, simple, advanced, subscriptions
from .advanced import auth, lists, sync, updates, episode, settings
from mygpo.users import converters
from mygpo.usersettings.converters import ScopeConverter

register_converter(converters.ClientUIDConverter, 'client-uid')
register_converter(converters.UsernameConverter, 'username')
register_converter(ScopeConverter, 'scope')


urlpatterns = [
    path('upload', legacy.upload),
    path('getlist', legacy.getlist),
    path(
        'subscriptions/<username:username>/' '<client-uid:device_uid>.<str:format>',
        simple.subscriptions,
        name='api-simple-subscriptions',
    ),
    path(
        'subscriptions/<username:username>.<str:format>',
        simple.all_subscriptions,
        name='api-all-subscriptions',
    ),
    path('search.<str:format>', simple.search),
    path(
        'suggestions/<int:count>.<str:format>',
        simple.suggestions,
        name='suggestions-opml',
    ),
    path(
        'toplist.opml',
        simple.toplist,
        kwargs={'count': 50, 'format': 'opml'},
        name='api-simple-toplist.opml',
    ),
    path('toplist/<int:count>.<str:format>', simple.toplist, name='api-simple-toplist'),
    path(
        'toplist.<str:format>',
        simple.toplist,
        kwargs={'count': 50},
        name='api-simple-toplist-50',
    ),
    path('gpodder-examples.<str:format>', simple.example_podcasts, name='example-opml'),
    path(
        'api/<int:version>/subscriptions/<username:username>/'
        '<client-uid:device_uid>.json',
        subscriptions.SubscriptionsAPI.as_view(),
        name='subscriptions-api',
    ),
    path('api/<int:version>/episodes/<username:username>.json', advanced.episodes),
    path(
        'api/<int:version>/devices/<username:username>/' '<client-uid:device_uid>.json',
        advanced.device,
    ),
    path('api/<int:version>/devices/<username:username>.json', advanced.devices),
    path('api/2/auth/<username:username>/login.json', auth.login),
    path('api/2/auth/<username:username>/logout.json', auth.logout),
    path('api/2/tags/<int:count>.json', advanced.directory.top_tags),
    path('api/2/tag/<str:tag>/<int:count>.json', advanced.directory.tag_podcasts),
    path('api/2/data/podcast.json', advanced.directory.podcast_info),
    path(
        'api/2/data/episode.json',
        advanced.directory.episode_info,
        name='api-episode-info',
    ),
    path('api/2/chapters/<username:username>.json', episode.ChaptersAPI.as_view()),
    path(
        'api/2/updates/<username:username>/<client-uid:device_uid>.json',
        updates.DeviceUpdates.as_view(),
    ),
    path(
        'api/2/settings/<username:username>/<scope:scope>.json',
        settings.SettingsAPI.as_view(),
        name='settings-api',
    ),
    path('api/2/favorites/<username:username>.json', advanced.favorites),
    path('api/2/lists/<username:username>/create.<str:format>', lists.create),
    path('api/2/lists/<username:username>.json', lists.get_lists),
    path(
        'api/2/lists/<username:username>/list/<slug:slug>.<str:format>',
        lists.podcast_list,
        name='api-get-list',
    ),
    path('api/2/sync-devices/<username:username>.json', sync.main),
]
