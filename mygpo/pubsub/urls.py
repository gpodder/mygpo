from django.urls import path

from . import views


urlpatterns = [
    path("subscribe", views.SubscribeView.as_view(), name="pubsub-subscribe")
]
