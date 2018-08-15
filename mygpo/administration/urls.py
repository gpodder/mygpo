from django.urls import path

from . import views


urlpatterns = [
    path('',
        views.Overview.as_view(),
        name='admin-overview'),

    path('hostinfo',
        views.HostInfo.as_view(),
        name='admin-hostinfo'),

    path('merge/',
        views.MergeSelect.as_view(),
        name='admin-merge'),

    path('merge/verify',
        views.MergeVerify.as_view(),
        name='admin-merge-verify'),

    path('merge/process',
        views.MergeProcess.as_view(),
        name='admin-merge-process'),

    path('merge/status/<uuid:task_id>',
        views.MergeStatus.as_view(),
        name='admin-merge-status'),

    path('clients',
        views.ClientStatsView.as_view(),
        name='clients'),

    path('clients.json',
        views.ClientStatsJsonView.as_view(),
        name='clients-json'),

    path('clients/user_agents',
        views.UserAgentStatsView.as_view(),
        name='useragents'),

    path('stats',
        views.StatsView.as_view(),
        name='stats'),

    path('stats.json',
        views.StatsJsonView.as_view(),
        name='stats-json'),

    path('activate-user',
        views.ActivateUserView.as_view(),
        name='admin-activate-user'),

    path('resend-activation-email',
        views.ResendActivationEmail.as_view(),
        name='admin-resend-activation'),

    path('make-publisher/input',
        views.MakePublisherInput.as_view(),
        name='admin-make-publisher-input'),

    path('make-publisher/process',
        views.MakePublisher.as_view(),
        name='admin-make-publisher'),

    path('make-publisher/result',
        views.MakePublisher.as_view(),
        name='admin-make-publisher-result'),

]
