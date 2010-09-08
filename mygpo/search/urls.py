from django.conf.urls.defaults import *

urlpatterns = patterns('mygpo.search.views',
 url(r'^$', 'search', name='search'),
)

