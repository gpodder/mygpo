from django.conf.urls.defaults import *

urlpatterns = patterns('mygpo.admin.views',
 url(r'^$',              'overview',          name='admin-overview'),
 url(r'^merge/$',        'merge_select',      name='admin-merge'),
 url(r'^merge/verify$',  'merge_verify',      name='admin-merge-verify'),
 url(r'^merge/process$', 'merge_process',     name='admin-merge-process'),
)
