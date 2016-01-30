from django.conf.urls import url

from . import views


urlpatterns = [

    url(r'^subscriptions/$',
        views.show_list,
        name='subscriptions'),

    url(r'^download/subscriptions\.opml$',
        views.download_all,
        name='subscriptions-opml'),

    url(r'^user/(?P<username>[\w.+-]+)/subscriptions/rss/$',
        views.subscriptions_feed,
        name='shared-subscriptions-rss'),

    url(r'^user/(?P<username>[\w.+-]+)/subscriptions$',
        views.for_user,
        name='shared-subscriptions'),

    url(r'^user/(?P<username>[\w.+-]+)/subscriptions\.opml$',
        views.for_user_opml,
        name='shared-subscriptions-opml'),

]
