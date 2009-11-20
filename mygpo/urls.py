import os.path
from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^mygpo/', include('mygpo.foo.urls')),
    (r'^$', 'mygpo.web.views.home'),
    (r'^login/$', 'mygpo.web.users.login_user'),
    (r'^logout/$', 'mygpo.web.users.logout_user'),
    (r'^migrate/$', 'mygpo.web.users.migrate_user'),
    (r'^register/$', 'mygpo.web.users.buildregister_user'),
    (r'^registered/$', 'mygpo.web.users.register_user'),
    (r'^registration_complete/$', 'django.views.generic.simple.direct_to_template', {'template': 'registration/registration_complete.html'}),
    (r'^activate/$', 'mygpo.web.users.activate_user'),
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
