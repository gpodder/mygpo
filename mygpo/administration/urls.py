from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$',
        views.Overview.as_view(),
        name='admin-overview'),

    url(r'^hostinfo$',
        views.HostInfo.as_view(),
        name='admin-hostinfo'),

    url(r'^merge/$',
        views.MergeSelect.as_view(),
        name='admin-merge'),

    url(r'^merge/verify$',
        views.MergeVerify.as_view(),
        name='admin-merge-verify'),

    url(r'^merge/process$',
        views.MergeProcess.as_view(),
        name='admin-merge-process'),

    url(r'^merge/status/(?P<task_id>[^/]+)$',
        views.MergeStatus.as_view(),
        name='admin-merge-status'),

    url(r'^clients$',
        views.ClientStatsView.as_view(),
        name='clients'),

    url(r'^clients\.json$',
        views.ClientStatsJsonView.as_view(),
        name='clients-json'),

    url(r'^clients/user_agents$',
        views.UserAgentStatsView.as_view(),
        name='useragents'),

    url(r'^stats$',
        views.StatsView.as_view(),
        name='stats'),

    url(r'^stats\.json$',
        views.StatsJsonView.as_view(),
        name='stats-json'),

    url(r'^activate-user/$',
        views.ActivateUserView.as_view(),
        name='admin-activate-user'),

    url(r'^make-publisher/input$',
        views.MakePublisherInput.as_view(),
        name='admin-make-publisher-input'),

    url(r'^make-publisher/process$',
        views.MakePublisher.as_view(),
        name='admin-make-publisher'),

    url(r'^make-publisher/result$',
        views.MakePublisher.as_view(),
        name='admin-make-publisher-result'),

]
