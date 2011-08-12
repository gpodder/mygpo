from django.conf.urls.defaults import *

urlpatterns = patterns('mygpo.publisher.views',
 url(r'^$',                             'home',                        name='publisher'),
 url(r'^(?P<username>[\w.-]+)/update',  'update_published_podcasts',   name='publisher-update'),
 url(r'^podcast/(?P<id>\d+)$',          'podcast',                     name='podcast-publisher-detail'),
 url(r'^podcast/(?P<id>\d+)/update$',   'update_podcast',              name='podcast-publisher-update'),
 url(r'^podcast/(?P<id>\d+)/episodes$', 'episodes',                    name='podcast-publisher-episodes'),

 url(r'^episode/(?P<id>\d+)$',
      'episode_oldid',               name='episode-publisher-detail'),

 url(r'^podcast/(?P<p_slug_id>[\w-]+)/(?P<e_slug_id>[\w-]+)$',
      'episode_slug_id',            name='episode-publisher-detail-slug-id'),

 url(r'^podcast/search$',               'search_podcast',              name='podcast-publisher-search'),
 url(r'^group/(?P<group_id>\d+)$',      'group',                       name='group-publisher'),
 url(r'^link/$',                        'link',                        name='link-here'),
 url(r'^advertise$',                    'advertise',                   name='advertise'),
)

