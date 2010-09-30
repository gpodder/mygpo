from django.conf.urls.defaults import *

urlpatterns = patterns('mygpo.directory.views',
 url(r'^directory/$',                                             'browse',                     name='directory-home'),
 url(r'^directory/(?P<category>[^/]+)$',                          'category',                   name='directory'),
)

