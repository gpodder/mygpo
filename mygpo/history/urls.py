from django.conf.urls import url

urlpatterns = [
 url(r'^history/$', 'mygpo.history.views.history', name='history'),

 url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/\+history',
     'mygpo.history.views.history_podcast_id',
     name='podcast-history-id'),

 url(r'^podcast/(?P<slug>[\w-]+)/\+history',
     'mygpo.history.views.history_podcast_slug',
     name='podcast-history-slug'),

 url(r'^device/(?P<uid>[\w.-]+)/history$', 'history', name='device-history'),
]
