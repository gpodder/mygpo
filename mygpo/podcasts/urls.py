from django.conf.urls import url

from .views import podcast, episode


urlpatterns = [

    url(r'^subscribe',
        podcast.subscribe_url,
        name='subscribe-by-url'),

    # Podcast Views with UUIDs
    url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/?$',
        podcast.show_id,
        name='podcast-id'),

    url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/subscribe$',
        podcast.subscribe_id,
        name='subscribe-id'),

    url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/subscribe/\+all$',
        podcast.subscribe_all_id,
        name='subscribe-all-id'),

    url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/unsubscribe/'
        '(?P<device_uid>[\w.-]+)',
        podcast.unsubscribe_id,
        name='unsubscribe-id'),

    url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/unsubscribe/\+all$',
        podcast.unsubscribe_all_id,
        name='unsubscribe-all-id'),

    url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/add-tag',
        podcast.add_tag_id,
        name='add-tag-id'),

    url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/remove-tag',
        podcast.remove_tag_id,
        name='remove-tag-id'),

    url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/set-public',
        podcast.set_public_id,
        name='podcast-public-id',
        kwargs={'public': True}),

    url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/set-private',
        podcast.set_public_id,
        name='podcast-private-id',
        kwargs={'public': False}),

    url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/-episodes',
        podcast.all_episodes_id,
        name='podcast-all-episodes-id'),

    url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/-flattr',
        podcast.flattr_podcast_id,
        name='podcast-flattr-id'),

    # Podcast Views with Slugs
    url(r'^podcast/(?P<slug>[\w-]+)/?$',
        podcast.show_slug,
        name='podcast-slug'),

    url(r'^podcast/(?P<slug>[\w-]+)/subscribe$',
        podcast.subscribe_slug,
        name='subscribe-slug'),

    url(r'^podcast/(?P<slug>[\w-]+)/subscribe/\+all$',
        podcast.subscribe_all_slug,
        name='subscribe-all-slug'),

    url(r'^podcast/(?P<slug>[\w-]+)/unsubscribe/(?P<device_uid>[\w.-]+)',
        podcast.unsubscribe_slug,
        name='unsubscribe-slug'),

    url(r'^podcast/(?P<slug>[\w-]+)/unsubscribe/\+all$',
        podcast.unsubscribe_all_slug,
        name='unsubscribe-all-slug'),

    url(r'^podcast/(?P<slug>[\w-]+)/add-tag',
        podcast.add_tag_slug,
        name='add-tag-slug'),

    url(r'^podcast/(?P<slug>[\w-]+)/remove-tag',
        podcast.remove_tag_slug,
        name='remove-tag-slug'),

    url(r'^podcast/(?P<slug>[\w-]+)/set-public',
        podcast.set_public_slug,
        name='podcast-public-slug',
        kwargs={'public': True}),

    url(r'^podcast/(?P<slug>[\w-]+)/set-private',
        podcast.set_public_slug,
        name='podcast-private-slug',
        kwargs={'public': False}),

    url(r'^podcast/(?P<slug>[\w-]+)/-episodes',
        podcast.all_episodes_slug,
        name='podcast-all-episodes-slug'),

    url(r'^podcast/(?P<slug>[\w-]+)/-flattr',
        podcast.flattr_podcast_slug,
        name='podcast-flattr-slug'),

    url(r'^favorites/$',
        episode.list_favorites,
        name='favorites'),

    # Episodes for UUIDs
    url(r'^podcast/(?P<p_id>[0-9a-f]{32})/(?P<e_id>[0-9a-f]{32})$',
        episode.show_id,
        name='episode-id'),

    url(r'^podcast/(?P<p_id>[0-9a-f]{32})/(?P<e_id>[0-9a-f]{32})/'
        'toggle-favorite',
        episode.toggle_favorite_id,
        name='episode-fav-id'),

    url(r'^podcast/(?P<p_id>[0-9a-f]{32})/(?P<e_id>[0-9a-f]{32})/add-action',
        episode.add_action_id,
        name='add-episode-action-id'),

    url(r'^podcast/(?P<p_id>[0-9a-f]{32})/(?P<e_id>[0-9a-f]{32})/-flattr',
        episode.flattr_episode_id,
        name='flattr-episode-id'),

    url(r'^podcast/(?P<p_id>[0-9a-f]{32})/(?P<e_id>[0-9a-f]{32})/\+history',
        episode.episode_history_id,
        name='episode-history-id'),

    # Episodes for Slugs
    url(r'^podcast/(?P<p_slug>[\w-]+)/(?P<e_slug>[\w-]+)$',
        episode.show_slug,
        name='episode-slug'),

    url(r'^podcast/(?P<p_slug>[\w-]+)/(?P<e_slug>[\w-]+)/toggle-favorite',
        episode.toggle_favorite_slug,
        name='episode-fav-slug'),

    url(r'^podcast/(?P<p_slug>[\w-]+)/(?P<e_slug>[\w-]+)/add-action',
        episode.add_action_slug,
        name='add-episode-action-slug'),

    url(r'^podcast/(?P<p_slug>[\w-]+)/(?P<e_slug>[\w-]+)/-flattr',
        episode.flattr_episode_slug,  name='flattr-episode-slug'),

    url(r'^podcast/(?P<p_slug>[\w-]+)/(?P<e_slug>[\w-]+)/\+history',
        episode.episode_history_slug,
        name='episode-history-slug'),

]
