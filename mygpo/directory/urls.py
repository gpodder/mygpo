from django.conf.urls import *

from mygpo.directory.views import DirectoryTopics, \
         AddPodcast, AddPodcastStatus, FlattrPodcastList, LicensePodcastList, \
         LicenseList, PodcastToplistView, EpisodeToplistView, CategoryView

urlpatterns = patterns('mygpo.directory.views',
 url(r'^toplist/$',
     PodcastToplistView.as_view(),
     name='toplist'),

 url(r'^toplist/episodes$',
     EpisodeToplistView.as_view(),
     name='episode-toplist'),

 url(r'^directory/$',
     DirectoryTopics.as_view(),
     name='directory-home'),

 url(r'^add-podcast/$',
     AddPodcast.as_view(),
     name='add-podcast'),

 url(r'^add-podcast/(?P<task_id>[^/]+)$',
     AddPodcastStatus.as_view(),
     name='add-podcast-status'),

 url(r'^directory/\+flattr$',
     FlattrPodcastList.as_view(),
     name='flattr-podcasts'),

 url(r'^directory/\+license$',
     LicenseList.as_view(),
     name='license-podcasts'),

 url(r'^directory/\+license/\+url/(?P<license_url>.+)$',
     LicensePodcastList.as_view(),
     name='license-podcasts-url'),

 url(r'^directory/(?P<category>.+)$',
     CategoryView.as_view(),
     name='directory'),
)
