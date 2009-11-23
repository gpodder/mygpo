import os.path
from django.conf.urls.defaults import *
from registration.views import activate, register
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
    (r'^register/$',  register, {'profile_callback': UserProfile.objects.create, 'success_url': '../registration_complete/' }),
    (r'^registration_complete/$', 'django.views.generic.simple.direct_to_template', {'template': 'registration/registration_complete.html'}),
    (r'^activate/(?P<activation_key>\w+)$', activate),
    (r'^info/$', 'django.views.generic.simple.direct_to_template', {'template': 'info.html'}),

    (r'^upload$', 'mygpo.api.legacy.upload'),
    (r'^getlist$', 'mygpo.api.legacy.getlist'),

    (r'^subscriptions/(?P<username>\w+)/(?P<device>\w+).(?P<format>(txt|opml|json))', 'mygpo.api.simple.subscriptions'),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/(.*)', admin.site.root),

    (r'^accounts/', include('registration.urls')),

    (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': os.path.abspath('%s/../htdocs/media/' % os.path.dirname(__file__))}),

)
