from django.conf.urls import url

from mygpo.history.views import (history, history_podcast_id,
    history_podcast_slug, )

urlpatterns = [
 url(r'^history/$', history, name='history'),

 url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/\+history',
     history_podcast_id,
     name='podcast-history-id'),

 url(r'^podcast/(?P<slug>[\w-]+)/\+history',
     history_podcast_slug,
     name='podcast-history-slug'),

 url(r'^device/(?P<uid>[\w.-]+)/history$', history, name='device-history'),
]
