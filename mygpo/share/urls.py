from django.urls import path, register_converter

from . import views, userpage

from mygpo.users import converters


register_converter(converters.UsernameConverter, "username")


urlpatterns = [
    path("share/", views.overview, name="share"),
    path(
        "share/subscriptions-public",
        views.set_token_public,
        kwargs={"public": True, "token_name": "subscriptions_token"},
        name="subscriptions-public",
    ),
    path(
        "share/subscriptions-private",
        views.set_token_public,
        kwargs={"public": False, "token_name": "subscriptions_token"},
        name="subscriptions-private",
    ),
    path(
        "share/favfeed-public",
        views.set_token_public,
        kwargs={"public": True, "token_name": "favorite_feeds_token"},
        name="favfeed-public",
    ),
    path(
        "share/favfeed-private",
        views.set_token_public,
        kwargs={"public": False, "token_name": "favorite_feeds_token"},
        name="favfeed-private",
    ),
    path(
        "share/userpage-public",
        views.set_token_public,
        kwargs={"public": True, "token_name": "userpage_token"},
        name="userpage-public",
    ),
    path(
        "share/userpage-private",
        views.set_token_public,
        kwargs={"public": False, "token_name": "userpage_token"},
        name="userpage-private",
    ),
    path("share/favorites", views.ShareFavorites.as_view(), name="share-favorites"),
    path(
        "favorites/private",
        views.FavoritesPublic.as_view(public=False),
        name="favorites_private",
    ),
    path(
        "favorites/public",
        views.FavoritesPublic.as_view(public=True),
        name="favorites_public",
    ),
    path(
        "share/subscriptions/private",
        views.PublicSubscriptions.as_view(public=False),
        name="private_subscriptions",
    ),
    path(
        "share/subscriptions/public",
        views.PublicSubscriptions.as_view(public=True),
        name="public_subscriptions",
    ),
    path(
        "share/favorites/create-directory-entry",
        views.FavoritesFeedCreateEntry.as_view(),
        name="favorites-create-entry",
    ),
    path("user/<username:username>/", userpage.UserpageView.as_view(), name="user"),
]
