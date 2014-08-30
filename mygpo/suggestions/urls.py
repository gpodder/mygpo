from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$',
        views.suggestions,
        name='suggestions'),

    url(r'^rate$',
        views.rate_suggestions,
        name='suggestions-rate'),

   url(r'^blacklist/(?P<slug>[\w-]+)$',
        views.blacklist,
        name='suggestions-blacklist-slug'),
]
