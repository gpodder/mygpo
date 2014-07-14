from django.conf.urls import *

urlpatterns = patterns('mygpo.publisher.views',
 url(r'^$',                             'home',                        name='publisher'),
 url(r'^(?P<username>[\w.-]+)/update$', 'update_published_podcasts',   name='publisher-update'),
 url(r'^(?P<username>[\w.-]+)/update-token', 'new_update_token',       name='publisher-new-update-token'),

 url(r'^podcast/(?P<slug>[\w-]+)/$',
      'podcast_slug',            name='podcast-publisher-detail-slug'),

 url(r'^podcast/(?P<slug>[\w-]+)/update$',
      'update_podcast_slug',    name='podcast-publisher-update-slug'),

 url(r'^podcast/(?P<slug>[\w-]+)/save$',
      'save_podcast_slug',    name='podcast-publisher-save-slug'),

 url(r'^podcast/(?P<slug>[\w-]+)/episodes$',
      'episodes_slug',           name='podcast-publisher-episodes-slug'),

 url(r'^podcast/(?P<p_slug>[\w-]+)/(?P<e_slug>[\w-]+)$',
      'episode_slug',            name='episode-publisher-detail-slug'),

 url(r'^podcast/(?P<p_slug>[\w-]+)/(?P<e_slug>[\w-]+)/set-slug$',
      'update_episode_slug_slug', name='publisher-set-episode-slug-slug'),


 url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/$',
      'podcast_id',            name='podcast-publisher-detail-id'),

 url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/update$',
      'update_podcast_id',    name='podcast-publisher-update-id'),

 url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/save$',
      'save_podcast_id',    name='podcast-publisher-save-id'),

 url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/episodes$',
      'episodes_id',           name='podcast-publisher-episodes-id'),

 url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/(?P<e_id>[0-9a-f]{32})$',
      'episode_id',            name='episode-publisher-detail-id'),

 url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/(?P<episode_id>[0-9a-f]{32})/set-slug$',
      'update_episode_slug_id', name='publisher-set-episode-slug-id'),


 url(r'^group/(?P<pg_slug>[\w-]+)$',    'group_slug',               name='group-publisher-slug'),


 url(r'^podcast/search$',               'search_podcast',              name='podcast-publisher-search'),
 url(r'^link/$',                        'link',                        name='link-here'),
 url(r'^advertise$',                    'advertise',                   name='advertise'),
)
