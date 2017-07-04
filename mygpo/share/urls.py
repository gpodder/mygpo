from django.conf.urls import url

from . import views, userpage


urlpatterns = [

    url(r'^share/$',
        views.overview,
        name='share'),

    url(r'^share/subscriptions-public$',
        views.set_token_public,
        kwargs={'public': True, 'token_name': 'subscriptions_token'},
        name='subscriptions-public'),

    url(r'^share/subscriptions-private$',
        views.set_token_public,
        kwargs={'public': False, 'token_name': 'subscriptions_token'},
        name='subscriptions-private'),

    url(r'^share/favfeed-public$',
        views.set_token_public,
        kwargs={'public': True, 'token_name': 'favorite_feeds_token'},
        name='favfeed-public'),

    url(r'^share/favfeed-private$',
        views.set_token_public,
        kwargs={'public': False, 'token_name': 'favorite_feeds_token'},
        name='favfeed-private'),

    url(r'^share/userpage-public$',
        views.set_token_public,
        kwargs={'public': True, 'token_name': 'userpage_token'},
        name='userpage-public'),

    url(r'^share/userpage-private$',
        views.set_token_public,
        kwargs={'public': False, 'token_name': 'userpage_token'},
        name='userpage-private'),

    url(r'^share/favorites$',
        views.ShareFavorites.as_view(),
        name='share-favorites'),

    url(r'^favorites/private',
        views.FavoritesPublic.as_view(public=False),
        name='favorites_private'),

    url(r'^favorites/public',
        views.FavoritesPublic.as_view(public=True),
        name='favorites_public'),

    url(r'^share/subscriptions/private',
        views.PublicSubscriptions.as_view(public=False),
        name='private_subscriptions'),

    url(r'^share/subscriptions/public',
        views.PublicSubscriptions.as_view(public=True),
        name='public_subscriptions'),

    url(r'^share/favorites/create-directory-entry',
        views.FavoritesFeedCreateEntry.as_view(),
        name='favorites-create-entry'),

    url(r'^user/(?P<username>[\w.+-]+)/?$',
        userpage.UserpageView.as_view(),
        name='user'),

]
