from django.urls import path, register_converter

from . import views

from mygpo.users import converters


register_converter(converters.UsernameConverter, "username")


urlpatterns = [
    path(
        "user/<username:username>/favorites.xml",
        views.favorite_feed,
        name="favorites-feed",
    )
]
