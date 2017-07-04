from django.conf.urls import url

from . import views


urlpatterns = [

    url(r'^$',
        views.suggestions,
        name='suggestions'),

    url(r'^blacklist/(?P<slug>[\w-]+)$',
        views.blacklist_slug,
        name='suggestions-blacklist-slug'),

    url(r'^blacklist/(?P<podcast_id>[0-9a-f]{32})$',
        views.blacklist_id,
        name='suggestions-blacklist-id'),

]
