import os.path
from django.urls import include, path, register_converter
from django.contrib import admin
from django.conf import settings
from django.contrib.staticfiles.views import serve

# strip the leading "/"
static_prefix = settings.STATIC_URL[1:]

# This URLs should be always be served, even during maintenance mode
urlpatterns = [
    path('%s<path:path>' % static_prefix, serve)
]



# Check for maintenace mode
from django.conf import settings
if settings.MAINTENANCE:
    from mygpo.web import utils
    urlpatterns += [
        path('', utils.maintenance),
    ]


# URLs are still registered during maintenace mode because we need to
# build links from them (eg login-link).
urlpatterns += [
    path('',                include('mygpo.web.urls')),
    path('',                include('mygpo.podcasts.urls')),
    path('',                include('mygpo.directory.urls')),
    path('',                include('mygpo.api.urls')),
    path('',                include('mygpo.userfeeds.urls')),
    path('',                include('mygpo.share.urls')),
    path('',                include('mygpo.history.urls')),
    path('',                include('mygpo.subscriptions.urls')),
    path('',                include('mygpo.users.urls')),
    path('',                include('mygpo.podcastlists.urls')),
    path('suggestions/',    include('mygpo.suggestions.urls')),
    path('publisher/',      include('mygpo.publisher.urls')),
    path('administration/', include('mygpo.administration.urls')),
    path('pubsub/',         include('mygpo.pubsub.urls')),
    path('admin/',          admin.site.urls),
]
