from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^favorites/$',
        views.FavoriteEpisodes.as_view(),
        name='favorites'),

]
