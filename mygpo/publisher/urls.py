from django.conf.urls import *

urlpatterns = patterns('mygpo.publisher.views',
 url(r'^$',                             'home',                        name='publisher'),
 url(r'^(?P<username>[\w.-]+)/update$', 'update_published_podcasts',   name='publisher-update'),
 url(r'^(?P<username>[\w.-]+)/update-token', 'new_update_token',       name='publisher-new-update-token'),

 url(r'^podcast/(?P<slug_id>[\w-]+)/$',
      'podcast_slug',            name='podcast-publisher-detail-slug'),

 url(r'^podcast/(?P<slug_id>[\w-]+)/update$',
      'update_podcast_slug',    name='podcast-publisher-update-slug'),

 url(r'^podcast/(?P<slug_id>[\w-]+)/save$',
      'save_podcast_slug',    name='podcast-publisher-save-slug'),

 url(r'^podcast/(?P<slug_id>[\w-]+)/episodes$',
      'episodes_slug',           name='podcast-publisher-episodes-slug'),

 url(r'^podcast/(?P<p_slug_id>[\w-]+)/(?P<e_slug_id>[\w-]+)$',
      'episode_slug',            name='episode-publisher-detail-slug'),

 url(r'^podcast/(?P<p_slug_id>[\w-]+)/(?P<e_slug_id>[\w-]+)/set-slug$',
      'update_episode_slug_slug', name='publisher-set-episode-slug-slug'),



 url(r'^group/(?P<slug_id>[\w-]+)$',    'group_slug',               name='group-publisher-slug'),


 url(r'^podcast/search$',               'search_podcast',              name='podcast-publisher-search'),
 url(r'^link/$',                        'link',                        name='link-here'),
 url(r'^advertise$',                    'advertise',                   name='advertise'),
)
