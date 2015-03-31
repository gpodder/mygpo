from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$',
        views.SuggestionsList.as_view(),
        name='suggestions'),

   url(r'^blacklist/(?P<slug>[\w-]+)$',
        views.BlacklistSuggestion.as_view(),
        name='suggestions-blacklist-slug'),

   url(r'^blacklist/(?P<podcast_id>[0-9a-f]{32})$',
        views.BlacklistSuggestion.as_view(),
        name='suggestions-blacklist-id'),
]
