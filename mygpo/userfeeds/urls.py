from django.conf.urls import url

from . import views


urlpatterns = [

    url(r'^user/(?P<username>[\w.+-]+)/favorites.xml$',
        views.favorite_feed,
        name='favorites-feed'),

]
