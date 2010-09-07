from django.conf.urls.defaults import *

urlpatterns = patterns('mygpo.userfeeds.views',
    (r'^user/(?P<username>\w+)/favorites.xml$', 'favorite_feed'),
)
