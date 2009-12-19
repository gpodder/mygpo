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
from registration.views import activate, register
from registration.forms import RegistrationFormUniqueEmail
from mygpo.api.models import UserProfile
from django.contrib.auth.views import logout

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^mygpo/', include('mygpo.foo.urls')),
    (r'^$', 'mygpo.web.views.home'),
    (r'^login/$', 'mygpo.web.users.login_user'),
    (r'^logout/$', logout, {'next_page': '/'}),
    (r'^migrate/$', 'mygpo.web.users.migrate_user'),
    (r'^register/$',  register, {'profile_callback': UserProfile.objects.create, 'success_url': '../registration_complete/', 'form_class': RegistrationFormUniqueEmail}),
    (r'^registration_complete/$', 'django.views.generic.simple.direct_to_template', {'template': 'registration/registration_complete.html'}),
    (r'^activate/(?P<activation_key>\w+)$', activate),
    (r'^podcast/(?P<pid>\w+)$', 'mygpo.web.views.podcast'),

    (r'account/$', 'mygpo.web.views.account'),
    (r'^info/$', 'django.views.generic.simple.direct_to_template', {'template': 'info.html'}),

    (r'^toplist/$', 'mygpo.web.views.toplist'),
    (r'^toplist/(?P<count>\d+).opml', 'mygpo.web.views.toplist_opml'),
    (r'^toplist.opml$', 'mygpo.web.views.toplist_opml', {'count': 50}),

    #Legacy API
    (r'^upload$', 'mygpo.api.legacy.upload'),
    (r'^getlist$', 'mygpo.api.legacy.getlist'),

    #Simple API
    (r'^subscriptions/(?P<username>\w+)/(?P<device_uid>\w+).(?P<format>(txt|opml|json))', 'mygpo.api.simple.subscriptions'),

    #Advanced API
    (r'^api/1/subscriptions/(?P<username>\w+)/(?P<device_uid>\w+).json', 'mygpo.api.advanced.subscriptions'),
    (r'^api/1/episodes/(?P<username>\w+).json', 'mygpo.api.advanced.episodes'),
    (r'^api/1/devices/(?P<username>\w+)/(?P<device_uid>\w+).json', 'mygpo.api.advanced.device'),
    (r'^api/1/devices/(?P<username>\w+)/devices.json', 'mygpo.api.advanced.devices'),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/(.*)', admin.site.root),

    (r'^accounts/', include('registration.urls')),

    (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': os.path.abspath('%s/../htdocs/media/' % os.path.dirname(__file__))}),

)

