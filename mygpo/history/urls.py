from django.conf.urls import url

from . import views

urlpatterns = [
 url(r'^history/$',
     views.History.as_view(),
     name='history'),

 url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/\+history',
     views.PodcastHistory.as_view(),
     name='podcast-history-id'),

 url(r'^device/(?P<uid>[\w.-]+)/history$',
     views.History.as_view(),
     name='device-history'),
]
