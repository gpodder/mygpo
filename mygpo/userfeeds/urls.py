from django.conf.urls import *

urlpatterns = patterns('mygpo.userfeeds.views',
 url(r'^user/(?P<username>[\w.+-]+)/favorites.xml$', 'favorite_feed', name='favorites-feed'),
)
