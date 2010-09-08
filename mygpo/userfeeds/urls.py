from django.conf.urls.defaults import *

urlpatterns = patterns('mygpo.userfeeds.views',
 url(r'^user/(?P<username>\w+)/favorites.xml$', 'favorite_feed', name='favorites-feed'),
)
