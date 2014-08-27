from django.conf.urls import url

urlpatterns = [
 url(r'^subscriptions/$',
     'mygpo.subscriptions.views.show_list',
     name='subscriptions'),

 url(r'^download/subscriptions\.opml$',
     'mygpo.subscriptions.views.download_all',
     name='subscriptions-opml'),

 url(r'^user/(?P<username>[\w.-]+)/subscriptions/rss/$',
     'mygpo.subscriptions.views.subscriptions_feed',
     name='shared-subscriptions-rss'),
]
