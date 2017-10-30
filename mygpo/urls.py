import os.path
from django.conf.urls import include, url
from django.contrib import admin
from django.conf import settings
from django.contrib.staticfiles.views import serve

# strip the leading "/"
static_prefix = settings.STATIC_URL[1:]

# This URLs should be always be served, even during maintenance mode
urlpatterns = [
 url(r'^%s(?P<path>.*)$' % static_prefix, serve)
]


# Check for maintenace mode
from django.conf import settings
if settings.MAINTENANCE:
    from mygpo.web import utils
    urlpatterns += [
     url(r'', utils.maintenance),
    ]


# URLs are still registered during maintenace mode because we need to
# build links from them (eg login-link).
urlpatterns += [
 url(r'^',           include('mygpo.web.urls')),
 url(r'^',           include('mygpo.podcasts.urls')),
 url(r'^',           include('mygpo.directory.urls')),
 url(r'^',           include('mygpo.api.urls')),
 url(r'^',           include('mygpo.userfeeds.urls')),
 url(r'^',           include('mygpo.share.urls')),
 url(r'^',           include('mygpo.history.urls')),
 url(r'^',           include('mygpo.subscriptions.urls')),
 url(r'^',           include('mygpo.users.urls')),
 url(r'^',           include('mygpo.podcastlists.urls')),
 url(r'^suggestions/', include('mygpo.suggestions.urls')),
 url(r'^publisher/', include('mygpo.publisher.urls')),
 url(r'^administration/', include('mygpo.administration.urls')),
 url(r'^pubsub/',    include('mygpo.pubsub.urls')),
 url(r'^admin/',     include(admin.site.urls)),
 url(r'^o/',         include('oauth2_provider.urls', namespace='oauth2_provider')),
]
