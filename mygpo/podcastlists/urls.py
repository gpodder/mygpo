from django.conf.urls import url

from . import views

urlpatterns = [

 url(r'^lists/$',
    views.PodcastListsOverview.as_view(),
    name='podcast-lists'),

 url(r'^share/lists/create$',
    views.create_list,
    name='list-create'),

 url(r'^user/(?P<username>[\w.+-]+)/lists/$',
    views.PodcastListsOfUser.as_view(),
    name='lists-user'),

 url(r'^user/(?P<username>[\w.+-]+)/list/(?P<slug>[\w-]+)$',
    views.PodcastListDetails.as_view(),
    name='list-show'),

 url(r'^user/(?P<username>[\w.+-]+)/list/(?P<slug>[\w-]+)\.opml$',
    views.list_opml,
    name='list-opml'),

 url(r'^user/(?P<username>[\w.+-]+)/list/(?P<slug>[\w-]+)/add/(?P<podcast_id>\w+)$',
    views.add_podcast,
    name='list-add-podcast'),

 url(r'^user/(?P<username>[\w.+-]+)/list/(?P<slug>[\w-]+)/remove/(?P<order>\d+)$',
    views.remove_podcast,
    name='list-remove-podcast'),

 url(r'^user/(?P<username>[\w.+-]+)/list/(?P<slug>[\w-]+)/delete$',
    views.delete_list,
    name='list-delete'),

 url(r'^user/(?P<username>[\w.+-]+)/list/(?P<slug>[\w-]+)/rate$',
    views.rate_list,
    name='list-rate'),
]
