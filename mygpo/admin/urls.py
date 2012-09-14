from django.conf.urls.defaults import *

from mygpo.admin.views import Overview, MergeSelect, MergeVerify, \
         MergeProcess, ClientStatsView, ClientStatsJsonView, \
         UserAgentStatsView, StatsView, StatsJsonView

urlpatterns = patterns('mygpo.admin.views',
 url(r'^$',              Overview.as_view(),     name='admin-overview'),
 url(r'^merge/$',        MergeSelect.as_view(),  name='admin-merge'),
 url(r'^merge/verify$',  MergeVerify.as_view(),  name='admin-merge-verify'),
 url(r'^merge/process$', MergeProcess.as_view(), name='admin-merge-process'),

 url(r'^clients$',             ClientStatsView.as_view(), name='clients'),
 url(r'^clients\.json$',       ClientStatsJsonView.as_view(), name='clients-json'),
 url(r'^clients/user_agents$', UserAgentStatsView.as_view(), name='useragents'),

 url(r'^stats$',        StatsView.as_view(), name='stats'),
 url(r'^stats\.json$',  StatsJsonView.as_view(), name='stats-json'),
)
