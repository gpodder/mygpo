from django.conf.urls import *

from mygpo.admin.views import Overview, MergeSelect, MergeVerify, \
         MergeProcess, MergeStatus, ClientStatsView, ClientStatsJsonView, \
         UserAgentStatsView, StatsView, StatsJsonView, HostInfo, \
         FiletypeStatsView, ActivateUserView

urlpatterns = patterns('mygpo.admin.views',
 url(r'^$',              Overview.as_view(),     name='admin-overview'),
 url(r'^hostinfo$',      HostInfo.as_view(),     name='admin-hostinfo'),
 url(r'^merge/$',        MergeSelect.as_view(),  name='admin-merge'),
 url(r'^merge/verify$',  MergeVerify.as_view(),  name='admin-merge-verify'),
 url(r'^merge/process$', MergeProcess.as_view(), name='admin-merge-process'),

 url(r'^merge/status/(?P<task_id>[^/]+)$',
     MergeStatus.as_view(),
     name='admin-merge-status'),

 url(r'^clients$',             ClientStatsView.as_view(), name='clients'),
 url(r'^clients\.json$',       ClientStatsJsonView.as_view(), name='clients-json'),
 url(r'^clients/user_agents$', UserAgentStatsView.as_view(), name='useragents'),

 url(r'^stats$',        StatsView.as_view(), name='stats'),
 url(r'^stats\.json$',  StatsJsonView.as_view(), name='stats-json'),

 url(r'^filetypes/$',
     FiletypeStatsView.as_view(),
     name='admin-filetypes'),

 url(r'^activate-user/$',
     ActivateUserView.as_view(),
     name='admin-activate-user'),
)
