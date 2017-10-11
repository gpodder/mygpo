from django.urls import path

from . import views


urlpatterns = [

    path('',
        views.suggestions,
        name='suggestions'),

    path('blacklist/<slug:slug>',
        views.blacklist_slug,
        name='suggestions-blacklist-slug'),

    path('blacklist/<uuid:podcast_id>',
        views.blacklist_id,
        name='suggestions-blacklist-id'),

]
