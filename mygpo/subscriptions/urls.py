from django.conf.urls import url

from . import views

urlpatterns = [
 url(r'^subscriptions/$',
     views.SubscriptionList.as_view(),
     name='subscriptions'),

 url(r'^user/(?P<username>[\w.+-]+)/subscriptions/rss/$',
     views.subscriptions_feed,
     name='shared-subscriptions-rss'),

 url(r'^user/(?P<username>[\w.+-]+)/subscriptions$',
     views.UserSubscriptions.as_view(),
     name='shared-subscriptions'),
]
