from django.conf.urls.defaults import *

from mygpo.admin.views import Overview, MergeSelect, MergeVerify, \
         MergeProcess, UserAgentStats

urlpatterns = patterns('mygpo.admin.views',
 url(r'^$',              Overview.as_view(),     name='admin-overview'),
 url(r'^merge/$',        MergeSelect.as_view(),  name='admin-merge'),
 url(r'^merge/verify$',  MergeVerify.as_view(),  name='admin-merge-verify'),
 url(r'^merge/process$', MergeProcess.as_view(), name='admin-merge-process'),

 url(r'^clients/user_agents$', UserAgentStats.as_view(), name='useragents'),
)
