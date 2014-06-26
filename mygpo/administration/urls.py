from django.conf.urls import *

from mygpo.administration.views import Overview, MergeSelect, MergeVerify, \
         MergeProcess, MergeStatus, ClientStatsView, ClientStatsJsonView, \
         UserAgentStatsView, StatsView, StatsJsonView, HostInfo, \
         ActivateUserView, MakePublisherInput, MakePublisher, \
         MakePublisherResult

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

 url(r'^activate-user/$',
     ActivateUserView.as_view(),
     name='admin-activate-user'),

 url(r'^make-publisher/input$',
     MakePublisherInput.as_view(),
     name='admin-make-publisher-input'),

 url(r'^make-publisher/process$',
     MakePublisher.as_view(),
     name='admin-make-publisher'),

 url(r'^make-publisher/result$',
     MakePublisher.as_view(),
     name='admin-make-publisher-result'),

)
