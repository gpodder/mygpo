from django.conf.urls import url
from django.contrib.auth.views import LogoutView
from django.views.generic.base import TemplateView

from .views import registration, settings, device, user


urlpatterns = [

    url(r'^register/$',
        registration.RegistrationView.as_view(),
        name='register'),

    url(r'^account/$',
        settings.account,
        name='account'),

    url(r'^account/privacy$',
        settings.privacy,
        name='privacy'),

    url(r'^account/profile$',
        settings.ProfileView.as_view(),
        name='profile'),

    url(r'^account/google/remove$',
        settings.AccountRemoveGoogle.as_view(),
        name='account-google-remove'),

    url(r'^account/privacy/default-public$',
        settings.DefaultPrivacySettings.as_view(public=True),
        name='privacy_default_public'),

    url(r'^account/privacy/default-private$',
        settings.DefaultPrivacySettings.as_view(public=False),
        name='privacy_default_private'),

    url(r'^account/privacy/(?P<podcast_id>[\w]+)/public$',
        settings.PodcastPrivacySettings.as_view(public=True),
        name='privacy_podcast_public'),

    url(r'^account/privacy/(?P<podcast_id>[\w]+)/private$',
        settings.PodcastPrivacySettings.as_view(public=False),
        name='privacy_podcast_private'),

    url(r'^account/delete$',
        settings.delete_account,
        name='delete-account'),

    url(r'^devices/$',
        device.overview,
        name='devices'),

    url(r'^devices/create-device$',
        device.create,
        name='device-create'),

    url(r'^device/(?P<uid>[\w.-]+)\.opml$',
        device.opml,
        name='device-opml'),

    url(r'^device/(?P<uid>[\w.-]+)$',
        device.show,
        name='device'),

    url(r'^device/(?P<uid>[\w.-]+)/symbian.opml$',
        device.symbian_opml,
        name='device-symbian-opml'),

    url(r'^device/(?P<uid>[\w.-]+)/sync$',
        device.sync,
        name='device-sync'),

    url(r'^device/(?P<uid>[\w.-]+)/unsync$',
        device.unsync,
        name='device-unsync'),

    url(r'^device/(?P<uid>[\w.-]+)/resync$',
        device.resync,
        name='trigger-sync'),

    url(r'^device/(?P<uid>[\w.-]+)/delete$',
        device.delete,
        name='device-delete'),

    url(r'^device/(?P<uid>[\w.-]+)/remove$',
        device.delete_permanently,
        name='device-delete-permanently'),

    url(r'^device/(?P<uid>[\w.-]+)/undelete$',
        device.undelete,
        name='device-undelete'),

    url(r'^device/(?P<uid>[\w.-]+)/edit$',
        device.edit,
        name='device-edit'),

    url(r'^device/(?P<uid>[\w.-]+)/update$',
        device.update,
        name='device-update'),

    url(r'^device/(?P<uid>[\w.-]+)/upload-opml$',
        device.upload_opml,
        name='device-upload-opml'),

    url(r'^register/restore_password$',
        user.restore_password,
        name='restore-password'),

    url(r'^login/$',
        user.LoginView.as_view(),
        name='login'),

    url(r'^login/google$',
        user.GoogleLogin.as_view(),
        name='login-google'),

    url(r'^login/oauth2callback$',
        user.GoogleLoginCallback.as_view(),
        name='login-google-callback'),

    url(r'^logout/$',
        LogoutView.as_view(),
        kwargs={'next_page': '/'},
        name='logout'),

]
