from django.conf.urls import url

from . import views

urlpatterns = [
 url(r'^history/$', views.history, name='history'),

 url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/\+history',
     views.history_podcast_id,
     name='podcast-history-id'),

 url(r'^podcast/(?P<slug>[\w-]+)/\+history',
     views.history_podcast_slug,
     name='podcast-history-slug'),

 url(r'^device/(?P<uid>[\w.-]+)/history$', views.history, name='device-history'),
]
