from django.conf.urls.defaults import *

from mygpo.admin.views import Overview, MergeSelect, MergeVerify, \
         MergeProcess

urlpatterns = patterns('mygpo.admin.views',
 url(r'^$',              Overview.as_view(),     name='admin-overview'),
 url(r'^merge/$',        MergeSelect.as_view(),  name='admin-merge'),
 url(r'^merge/verify$',  MergeVerify.as_view(),  name='admin-merge-verify'),
 url(r'^merge/process$', MergeProcess.as_view(), name='admin-merge-process'),
)
