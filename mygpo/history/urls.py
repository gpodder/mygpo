from django.urls import path

from . import views
from mygpo import converters

urlpatterns = [
    path("history/", views.history, name="history"),
    path(
        "podcast/<uuid:podcast_id>/+history",
        views.history_podcast_id,
        name="podcast-history-id",
    ),
    path(
        "podcast/<slug:slug>/+history",
        views.history_podcast_slug,
        name="podcast-history-slug",
    ),
    path("device/<client-uid:uid>/history", views.history, name="device-history"),
]
