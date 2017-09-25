from django.conf.urls import url

from . import views


urlpatterns = [

    url(r'^$',
        views.home,
        name='publisher'),

    url(r'^(?P<username>[\w.+-]+)/update$',
        views.update_published_podcasts,
        name='publisher-update'),

    url(r'^(?P<username>[\w.+-]+)/update-token',
        views.new_update_token,
        name='publisher-new-update-token'),

    url(r'^podcast/(?P<slug>[\w-]+)/$',
        views.podcast_slug,
        name='podcast-publisher-detail-slug'),

    url(r'^podcast/(?P<slug>[\w-]+)/update$',
        views.update_podcast_slug,
        name='podcast-publisher-update-slug'),

    url(r'^podcast/(?P<slug>[\w-]+)/save$',
        views.save_podcast_slug,
        name='podcast-publisher-save-slug'),

    url(r'^podcast/(?P<slug>[\w-]+)/episodes$',
        views.episodes_slug,
        name='podcast-publisher-episodes-slug'),

    url(r'^podcast/(?P<p_slug>[\w-]+)/(?P<e_slug>[\w-]+)$',
        views.episode_slug,
        name='episode-publisher-detail-slug'),

    url(r'^podcast/(?P<p_slug>[\w-]+)/(?P<e_slug>[\w-]+)/set-slug$',
        views.update_episode_slug_slug,
        name='publisher-set-episode-slug-slug'),

    url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/$',
        views.podcast_id,
        name='podcast-publisher-detail-id'),

    url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/update$',
        views.update_podcast_id,
        name='podcast-publisher-update-id'),

    url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/save$',
        views.save_podcast_id,
        name='podcast-publisher-save-id'),

    url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/episodes$',
        views.episodes_id,
        name='podcast-publisher-episodes-id'),

    url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/(?P<e_id>[0-9a-f]{32})$',
        views.episode_id,
        name='episode-publisher-detail-id'),

    url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/(?P<episode_id>[0-9a-f]{32})/'
        'set-slug$',
        views.update_episode_slug_id,
        name='publisher-set-episode-slug-id'),

    url(r'^group/(?P<pg_slug>[\w-]+)$',
        views.group_slug,
        name='group-publisher-slug'),

    url(r'^group/(?P<pg_slug>[\w-]+)$',
        views.group_id,
        name='group-publisher-id'),

    url(r'^podcast/search$',
        views.search_podcast,
        name='podcast-publisher-search'),

    url(r'^link/$',
        views.link,
        name='link-here'),

    url(r'^advertise$',
        views.advertise,
        name='advertise'),

]
