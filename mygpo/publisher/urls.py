from django.urls import path, register_converter

from . import views

from mygpo.users import converters


register_converter(converters.UsernameConverter, 'username')


urlpatterns = [
    path('', views.home, name='publisher'),
    path(
        '<username:username>/update',
        views.update_published_podcasts,
        name='publisher-update',
    ),
    path(
        '<username:username>/update-token',
        views.new_update_token,
        name='publisher-new-update-token',
    ),
    path(
        'podcast/<uuid:podcast_id>/',
        views.podcast_id,
        name='podcast-publisher-detail-id',
    ),
    path(
        'podcast/<uuid:podcast_id>/update',
        views.update_podcast_id,
        name='podcast-publisher-update-id',
    ),
    path(
        'podcast/<uuid:podcast_id>/save',
        views.save_podcast_id,
        name='podcast-publisher-save-id',
    ),
    path(
        'podcast/<uuid:podcast_id>/episodes',
        views.episodes_id,
        name='podcast-publisher-episodes-id',
    ),
    path(
        'podcast/<uuid:podcast_id>/<uuid:e_id>',
        views.episode_id,
        name='episode-publisher-detail-id',
    ),
    path(
        'podcast/<uuid:podcast_id>/<uuid:episode_id>/' 'set-slug',
        views.update_episode_slug_id,
        name='publisher-set-episode-slug-id',
    ),
    path(
        'podcast/<slug:slug>/', views.podcast_slug, name='podcast-publisher-detail-slug'
    ),
    path(
        'podcast/<slug:slug>/update',
        views.update_podcast_slug,
        name='podcast-publisher-update-slug',
    ),
    path(
        'podcast/<slug:slug>/save',
        views.save_podcast_slug,
        name='podcast-publisher-save-slug',
    ),
    path(
        'podcast/<slug:slug>/episodes',
        views.episodes_slug,
        name='podcast-publisher-episodes-slug',
    ),
    path(
        'podcast/<slug:p_slug>/<slug:e_slug>',
        views.episode_slug,
        name='episode-publisher-detail-slug',
    ),
    path(
        'podcast/<slug:p_slug>/<slug:e_slug>/set-slug',
        views.update_episode_slug_slug,
        name='publisher-set-episode-slug-slug',
    ),
    path('group/<slug:pg_slug>', views.group_slug, name='group-publisher-slug'),
    path('group/<slug:pg_slug>', views.group_id, name='group-publisher-id'),
    path('podcast/search', views.search_podcast, name='podcast-publisher-search'),
    path('link/', views.link, name='link-here'),
    path('advertise', views.advertise, name='advertise'),
]
