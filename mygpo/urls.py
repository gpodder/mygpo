from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^mygpo/', include('mygpo.foo.urls')),
    (r'^$', 'mygpo.web.views.home'),
    (r'^info/$', 'django.views.generic.simple.direct_to_template', {'template': 'info.html'}),

    (r'^upload$', 'mygpo.api.legacy.upload'),
    (r'^getlist$', 'mygpo.api.legacy.getlist'),
 
    (r'^subscriptions/(?P<username>\w+)/default.(?P<format>\w+)', 'mygpo.api.simple.all_subscriptions'),
    (r'^subscriptions/(?P<username>\w+)/(?P<device>\w+).(?P<format>\w+)', 'mygpo.api.simple.device_subscription'),
    
    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/(.*)', admin.site.root),
)
