from django.conf.urls.defaults import *

urlpatterns = patterns('mygpo.publisher.views',
    (r'^$',                             'home'),
    (r'^(?P<username>\w+)/update',      'update_published_podcasts'),
    (r'^podcast/(?P<id>\d+)$',          'podcast'),
    (r'^podcast/(?P<id>\d+)/update$',   'update_podcast'),
    (r'^podcast/(?P<id>\d+)/episodes$', 'episodes'),
    (r'^episode/(?P<id>\d+)$',          'episode'),
    (r'^podcast/search$',               'search_podcast'),
    (r'^group/(?P<group_id>\d+)$',      'group'),
    (r'^link/$',                        'link'),
    (r'^advertise$',                    'advertise'),
)

