from django.urls import path

from . import views

from mygpo import converters


urlpatterns = [
    path(
        "user/<username:username>/favorites.xml",
        views.favorite_feed,
        name="favorites-feed",
    )
]
