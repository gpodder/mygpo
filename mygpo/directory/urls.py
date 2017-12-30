from django.conf.urls import url

from . import views


urlpatterns = [

    url(r'^toplist/$',
        views.PodcastToplistView.as_view(),
        name='toplist'),

    url(r'^trending/$',
        views.TrendingPodcastsView.as_view(),
        name='trending'),

    url(r'^toplist/episodes$',
        views.EpisodeToplistView.as_view(),
        name='episode-toplist'),

    url(r'^directory/$',
        views.Directory.as_view(),
        name='directory-home'),

    url(r'^carousel/$',
        views.Carousel.as_view(),
        name='carousel-demo'),

    url(r'^missing/$',
        views.MissingPodcast.as_view(),
        name='missing-podcast'),

    url(r'^add-podcast/$',
        views.AddPodcast.as_view(),
        name='add-podcast'),

    url(r'^add-podcast/(?P<task_id>[^/]+)$',
        views.AddPodcastStatus.as_view(),
        name='add-podcast-status'),

    url(r'^directory/\+license$',
        views.LicenseList.as_view(),
        name='license-podcasts'),

    url(r'^directory/\+license/\+url/(?P<license_url>.+)$',
        views.LicensePodcastList.as_view(),
        name='license-podcasts-url'),

    url(r'^directory/(?P<category>.+)$',
        views.category,
        name='directory'),

    url(r'^search/$',
        views.search,
        name='search'),

    url(r'^lists/$',
        views.podcast_lists,
        name='podcast-lists'),

]
