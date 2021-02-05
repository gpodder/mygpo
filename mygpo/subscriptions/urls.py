from django.urls import path, register_converter

from . import views

from mygpo.users import converters


register_converter(converters.UsernameConverter, "username")


urlpatterns = [
    path("subscriptions/", views.show_list, name="subscriptions"),
    path("download/subscriptions.opml", views.download_all, name="subscriptions-opml"),
    path(
        "user/<username:username>/subscriptions/rss/",
        views.subscriptions_feed,
        name="shared-subscriptions-rss",
    ),
    path(
        "user/<username:username>/subscriptions",
        views.for_user,
        name="shared-subscriptions",
    ),
    path(
        "user/<username:username>/subscriptions.opml",
        views.for_user_opml,
        name="shared-subscriptions-opml",
    ),
]
