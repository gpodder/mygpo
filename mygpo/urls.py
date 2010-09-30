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
from django.conf.urls.defaults import *

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^',           include('mygpo.web.urls')),
    (r'^',           include('mygpo.directory.urls')),
    (r'^',           include('mygpo.api.urls')),
    (r'^',           include('mygpo.userfeeds.urls')),
    (r'^search/',    include('mygpo.search.urls')),
    (r'^accounts/',  include('registration.urls')),
    (r'^publisher/', include('mygpo.publisher.urls')),

    (r'^admin/(.*)', admin.site.root),
    (r'^media/(?P<path>.*)$', 'django.views.static.serve',
         {'document_root': os.path.abspath('%s/../htdocs/media/' % os.path.dirname(__file__))}),
)

