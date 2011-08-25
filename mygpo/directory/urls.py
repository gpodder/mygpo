from django.conf.urls.defaults import *

urlpatterns = patterns('mygpo.directory.views',
 url(r'^toplist/$',                                               'toplist',                    name='toplist'),
 url(r'^toplist/episodes$',                                       'episode_toplist',            name='episode-toplist'),
 url(r'^directory/$',                                             'browse',                     name='directory-home'),
 url(r'^directory/(?P<category>.+)$',                          'category',                   name='directory'),
 url(r'^search/$',                        'search',      name='search'),
 url(r'^lists/$',                     'podcast_lists', name='podcast-lists'),
)

