from django.urls import path, register_converter, include

from . import views

from mygpo.users import converters


register_converter(converters.UsernameConverter, 'username')


userpatterns = [

    path('lists/',
        views.lists_user,
        name='lists-user'),

    path('list/<slug:slug>',
        views.list_show,
        name='list-show'),

    path('list/<slug:slug>.opml',
        views.list_opml,
        name='list-opml'),

    path('list/<slug:slug>/search',
        views.search,
        name='list-search'),

    path('list/<slug:slug>/add/<uuid:podcast_id>',
        views.add_podcast,
        name='list-add-podcast'),

    path('list/<slug:slug>/remove/<int:order>',
        views.remove_podcast,
        name='list-remove-podcast'),

    path('list/<slug:slug>/delete',
        views.delete_list,
        name='list-delete'),

    path('list/<slug:slug>/rate',
        views.rate_list,
        name='list-rate'),

]


urlpatterns = [

    path('share/lists/',
        views.lists_own,
        name='lists-overview'),

    path('share/lists/create',
        views.create_list,
        name='list-create'),

    path('user/<username:username>/',
        include(userpatterns)),

]
