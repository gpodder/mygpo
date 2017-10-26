from django.urls import path, register_converter, include

from .views import podcast, episode
from mygpo.users import converters


register_converter(converters.ClientUIDConverter, 'client-uid')


podcast_uuid_patterns = [

    path('subscribe',
        podcast.subscribe_id,
        name='subscribe-id'),

    path('subscribe/+all',
        podcast.subscribe_all_id,
        name='subscribe-all-id'),

    path('unsubscribe/<client-uid:device_uid>',
        podcast.unsubscribe_id,
        name='unsubscribe-id'),

    path('unsubscribe/+all',
        podcast.unsubscribe_all_id,
        name='unsubscribe-all-id'),

    path('add-tag',
        podcast.add_tag_id,
        name='add-tag-id'),

    path('remove-tag',
        podcast.remove_tag_id,
        name='remove-tag-id'),

    path('set-public',
        podcast.set_public_id,
        name='podcast-public-id',
        kwargs={'public': True}),

    path('set-private',
        podcast.set_public_id,
        name='podcast-private-id',
        kwargs={'public': False}),

    path('-episodes',
        podcast.all_episodes_id,
        name='podcast-all-episodes-id'),

]

podcast_slug_patterns = [

    path('subscribe',
        podcast.subscribe_slug,
        name='subscribe-slug'),

    path('subscribe/+all',
        podcast.subscribe_all_slug,
        name='subscribe-all-slug'),

    path('unsubscribe/<client-uid:device_uid>',
        podcast.unsubscribe_slug,
        name='unsubscribe-slug'),

    path('unsubscribe/+all',
        podcast.unsubscribe_all_slug,
        name='unsubscribe-all-slug'),

    path('add-tag',
        podcast.add_tag_slug,
        name='add-tag-slug'),

    path('remove-tag',
        podcast.remove_tag_slug,
        name='remove-tag-slug'),

    path('set-public',
        podcast.set_public_slug,
        name='podcast-public-slug',
        kwargs={'public': True}),

    path('set-private',
        podcast.set_public_slug,
        name='podcast-private-slug',
        kwargs={'public': False}),

    path('-episodes',
        podcast.all_episodes_slug,
        name='podcast-all-episodes-slug'),

]


episode_uuid_patterns = [

    path('toggle-favorite',
        episode.toggle_favorite_id,
        name='episode-fav-id'),

    path('add-action',
        episode.add_action_id,
        name='add-episode-action-id'),

    path('+history',
        episode.episode_history_id,
        name='episode-history-id'),

]


episode_slug_patterns = [

    path('toggle-favorite',
        episode.toggle_favorite_slug,
        name='episode-fav-slug'),

    path('add-action',
        episode.add_action_slug,
        name='add-episode-action-slug'),

    path('+history',
        episode.episode_history_slug,
        name='episode-history-slug'),

]

urlpatterns = [

    path('subscribe',
        podcast.subscribe_url,
        name='subscribe-by-path'),

    # Podcast Views with UUIDs
    path('podcast/<uuid:podcast_id>',
        podcast.show_id,
        name='podcast-id'),

    path('podcast/<uuid:podcast_id>/',
        include(podcast_uuid_patterns)),

    # Podcast Views with Slugs
    path('podcast/<slug:slug>',
        podcast.show_slug,
        name='podcast-slug'),

    path('podcast/<slug:slug>/',
        include(podcast_slug_patterns)),

    path('favorites/',
        episode.list_favorites,
        name='favorites'),

    # Episodes for UUIDs
    path('podcast/<uuid:p_id>/<uuid:e_id>',
        episode.show_id,
        name='episode-id'),

    path('podcast/<uuid:p_id>/<uuid:e_id>/',
        include(episode_uuid_patterns)),


    # Episodes for Slugs
    path('podcast/<slug:p_slug>/<slug:e_slug>',
        episode.show_slug,
        name='episode-slug'),

    path('podcast/<slug:p_slug>/<slug:e_slug>/',
        include(episode_slug_patterns)),

]
