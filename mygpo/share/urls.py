from django.conf.urls import *

from mygpo.share.views import ShareFavorites, FavoritesPublic, \
         PublicSubscriptions, FavoritesFeedCreateEntry
from mygpo.share.userpage import UserpageView


urlpatterns = patterns('mygpo.share.views',
 url(r'^share/$',
                     'overview',                  name='share'),
 url(r'^share/subscriptions-public$',
                     'set_token_public',
                     {'public': True, 'token_name': 'subscriptions_token'},
                                                  name='subscriptions-public'),
 url(r'^share/subscriptions-private$',
                     'set_token_public',
                     {'public': False, 'token_name': 'subscriptions_token'},
                                                  name='subscriptions-private'),
 url(r'^share/favfeed-public$',
                     'set_token_public',
                     {'public': True, 'token_name': 'favorite_feeds_token'},
                                                  name='favfeed-public'),
 url(r'^share/favfeed-private$',
                     'set_token_public',
                     {'public': False, 'token_name': 'favorite_feeds_token'},
                                                  name='favfeed-private'),
 url(r'^share/userpage-public$',
                     'set_token_public',
                     {'public': True, 'token_name': 'userpage_token'},
                                                  name='userpage-public'),
 url(r'^share/userpage-private$',
                     'set_token_public',
                     {'public': False, 'token_name': 'userpage_token'},
                                                  name='userpage-private'),
 url(r'^share/lists/$',
                     'lists_own',                 name='lists-overview'),
 url(r'^share/lists/create$',
                     'create_list',               name='list-create'),
 url(r'^user/(?P<username>[\w.-]+)/lists/$',
                     'lists_user',                name='lists-user'),
 url(r'^user/(?P<username>[\w.-]+)/list/(?P<listname>[\w-]+)$',
                     'list_show',                 name='list-show'),
 url(r'^user/(?P<username>[\w.-]+)/list/(?P<listname>[\w-]+)\.opml$',
                     'list_opml',                 name='list-opml'),
 url(r'^user/(?P<username>[\w.-]+)/list/(?P<listname>[\w-]+)/search$',
                     'search',                    name='list-search'),
 url(r'^user/(?P<username>[\w.-]+)/list/(?P<listname>[\w-]+)/add/(?P<podcast_id>\w+)$',
                     'add_podcast',               name='list-add-podcast'),
 url(r'^user/(?P<username>[\w.-]+)/list/(?P<listname>[\w-]+)/remove/(?P<podcast_id>\w+)$',
                     'remove_podcast',            name='list-remove-podcast'),
 url(r'^user/(?P<username>[\w.-]+)/list/(?P<listname>[\w-]+)/delete$',
                     'delete_list',               name='list-delete'),
 url(r'^user/(?P<username>[\w.-]+)/list/(?P<listname>[\w-]+)/rate$',
                     'rate_list',                 name='list-rate'),


 url(r'^share/favorites$',
         ShareFavorites.as_view(),
         name='share-favorites',
    ),

 url(r'^favorites/private',
     FavoritesPublic.as_view(public=False),
     name='favorites_private'),

 url(r'^favorites/public',
     FavoritesPublic.as_view(public=True),
     name='favorites_public'),

 url(r'^share/subscriptions/private',
     PublicSubscriptions.as_view(public=False),
     name='private_subscriptions'),

 url(r'^share/subscriptions/public',
     PublicSubscriptions.as_view(public=True),
     name='public_subscriptions'),

 url(r'^share/favorites/create-directory-entry',
     FavoritesFeedCreateEntry.as_view(),
     name='favorites-create-entry'),

)

urlpatterns += patterns('mygpo.share.userpage',
 url(r'^user/(?P<username>[\w.-]+)/?$', UserpageView.as_view(), name='user'),
 )
