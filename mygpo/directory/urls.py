from django.urls import path

from . import views


urlpatterns = [
    path('toplist/', views.PodcastToplistView.as_view(), name='toplist'),
    path(
        'toplist/episodes', views.EpisodeToplistView.as_view(), name='episode-toplist'
    ),
    path('directory/', views.Directory.as_view(), name='directory-home'),
    path('carousel/', views.Carousel.as_view(), name='carousel-demo'),
    path('missing/', views.MissingPodcast.as_view(), name='missing-podcast'),
    path('add-podcast/', views.AddPodcast.as_view(), name='add-podcast'),
    path(
        'add-podcast/<uuid:task_id>',
        views.AddPodcastStatus.as_view(),
        name='add-podcast-status',
    ),
    path('directory/+license', views.LicenseList.as_view(), name='license-podcasts'),
    path(
        'directory/+license/+url/<path:license_url>',
        views.LicensePodcastList.as_view(),
        name='license-podcasts-url',
    ),
    path('directory/<path:category>', views.category, name='directory'),
    path('search/', views.search, name='search'),
    path('lists/', views.podcast_lists, name='podcast-lists'),
]
