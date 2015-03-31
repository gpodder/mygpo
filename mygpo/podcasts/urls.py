from django.conf.urls import *
from django.contrib.auth.views import logout
from django.views.generic.base import TemplateView, RedirectView


from mygpo.web.views.podcast import SubscribePodcast

urlpatterns += patterns('mygpo.podcasts.views',
 url(r'^subscribe',
     'subscribe_url',
     name='subscribe-by-url'),

 # Podcast Views with UUIDs
 url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/?$',
     'show_id',
     name='podcast-id'),

 url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/subscribe$',
     SubscribePodcast.as_view(),
     name='subscribe-id'),

 url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/subscribe/\+all$',
     'subscribe_all_id',
     name='subscribe-all-id'),

 url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/unsubscribe/(?P<device_uid>[\w.-]+)',
     'unsubscribe_id',
     name='unsubscribe-id'),

 url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/unsubscribe/\+all$',
     'unsubscribe_all_id',
     name='unsubscribe-all-id'),

 url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/add-tag',
     'add_tag_id',
     name='add-tag-id'),

 url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/remove-tag',
     'remove_tag_id',
     name='remove-tag-id'),

 url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/set-public',
     'set_public_id',
     name='podcast-public-id',
     kwargs={'public': True}),

 url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/set-private',
     'set_public_id',
     name='podcast-private-id',
     kwargs={'public': False}),

 url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/-episodes',
     'all_episodes_id',
     name='podcast-all-episodes-id'),

 url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/-flattr',
     'flattr_podcast_id',
     name='podcast-flattr-id'),


 # Podcast Views with Slugs
 url(r'^podcast/(?P<slug>[\w-]+)/?$',
     'show_slug',
     name='podcast-slug'),

 url(r'^podcast/(?P<slug>[\w-]+)/subscribe$',
     SubscribePodcast.as_view(),
     name='subscribe-slug'),

 url(r'^podcast/(?P<slug>[\w-]+)/subscribe/\+all$',
     'subscribe_all_slug',
     name='subscribe-all-slug'),

 url(r'^podcast/(?P<slug>[\w-]+)/unsubscribe/(?P<device_uid>[\w.-]+)',
     'unsubscribe_slug',
     name='unsubscribe-slug'),

 url(r'^podcast/(?P<slug>[\w-]+)/unsubscribe/\+all$',
     'unsubscribe_all_slug',
     name='unsubscribe-all-slug'),

 url(r'^podcast/(?P<slug>[\w-]+)/add-tag',
     'add_tag_slug',
     name='add-tag-slug'),

 url(r'^podcast/(?P<slug>[\w-]+)/remove-tag',
     'remove_tag_slug',
     name='remove-tag-slug'),

 url(r'^podcast/(?P<slug>[\w-]+)/set-public',
     'set_public_slug',
     name='podcast-public-slug',
     kwargs={'public': True}),

 url(r'^podcast/(?P<slug>[\w-]+)/set-private',
     'set_public_slug',
     name='podcast-private-slug',
     kwargs={'public': False}),

 url(r'^podcast/(?P<slug>[\w-]+)/-episodes',
     'all_episodes_slug',
     name='podcast-all-episodes-slug'),

 url(r'^podcast/(?P<slug>[\w-]+)/-flattr',
     'flattr_podcast_slug',
     name='podcast-flattr-slug'),
)
