from django.conf.urls import patterns, url

from mygpo.pubsub.views import SubscribeView


urlpatterns = patterns('',
 url(r'^subscribe$',      SubscribeView.as_view(),   name='pubsub-subscribe'),
)
