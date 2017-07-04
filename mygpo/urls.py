#
# This file is part of my.gpodder.org.
#
# my.gpodder.org is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# my.gpodder.org is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public
# License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with my.gpodder.org. If not, see <http://www.gnu.org/licenses/>.
#

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
]
