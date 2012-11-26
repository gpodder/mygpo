from django.conf.urls.defaults import *

urlpatterns = patterns('mygpo.publisher.views',
 url(r'^$',                             'home',                        name='publisher'),
 url(r'^(?P<username>[\w.-]+)/update$', 'update_published_podcasts',   name='publisher-update'),
 url(r'^(?P<username>[\w.-]+)/update-token', 'new_update_token',       name='publisher-new-update-token'),

 url(r'^podcast/(?P<pid>\d+)$',          'podcast_oldid',              name='podcast-publisher-detail'),
 url(r'^podcast/(?P<pid>\d+)/update$',   'update_podcast_oldid',       name='podcast-publisher-update'),
 url(r'^podcast/(?P<pid>\d+)/save$',     'save_podcast_oldid',       name='podcast-publisher-save'),
 url(r'^podcast/(?P<pid>\d+)/episodes$', 'episodes_oldid',             name='podcast-publisher-episodes'),


 url(r'^episode/(?P<id>\d+)$',
      'episode_oldid',               name='episode-publisher-detail'),


 url(r'^podcast/(?P<slug_id>[\w-]+)/$',
      'podcast_slug_id',            name='podcast-publisher-detail-slug-id'),

 url(r'^podcast/(?P<slug_id>[\w-]+)/update$',
      'update_podcast_slug_id' ,    name='podcast-publisher-update-slug-id'),

 url(r'^podcast/(?P<slug_id>[\w-]+)/save$',
      'save_podcast_slug_id' ,    name='podcast-publisher-save-slug-id'),

 url(r'^podcast/(?P<slug_id>[\w-]+)/episodes$',
      'episodes_slug_id',           name='podcast-publisher-episodes-slug-id'),

 url(r'^podcast/(?P<p_slug_id>[\w-]+)/(?P<e_slug_id>[\w-]+)$',
      'episode_slug_id',            name='episode-publisher-detail-slug-id'),

 url(r'^group/(?P<group_id>\d+)$',      'group_oldid',                 name='group-publisher'),
 url(r'^group/(?P<slug_id>[\w-]+)$',    'group_slug_id',               name='group-publisher-slug-id'),


 url(r'^podcast/search$',               'search_podcast',              name='podcast-publisher-search'),
 url(r'^link/$',                        'link',                        name='link-here'),
 url(r'^advertise$',                    'advertise',                   name='advertise'),
)

