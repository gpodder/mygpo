from django.conf.urls.defaults import *

urlpatterns = patterns('mygpo.search.views',
    (r'^$', 'search'),
)

