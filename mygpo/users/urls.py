from django.urls import path, register_converter
from django.contrib.auth.views import LogoutView
from django.views.generic.base import TemplateView

from .views import registration, settings, device, user
from mygpo.users import converters

register_converter(converters.ClientUIDConverter, 'client-uid')


urlpatterns = [

    path('register/',
        registration.RegistrationView.as_view(),
        name='register'),

    path('registration_complete/',
        registration.TemplateView.as_view(
            template_name='registration/registration_complete.html'),
        name='registration-complete'),

    path('activate/<str:activation_key>',
        registration.ActivationView.as_view()),

    path('registration/resend',
        registration.ResendActivationView.as_view(),
        name='resend-activation'),

    path('registration/resent',
        registration.ResentActivationView.as_view(),
        name='resent-activation'),

    path('account/',
        settings.account,
        name='account'),

    path('account/privacy',
        settings.privacy,
        name='privacy'),

    path('account/profile',
        settings.ProfileView.as_view(),
        name='profile'),

    path('account/google/remove',
        settings.AccountRemoveGoogle.as_view(),
        name='account-google-remove'),

    path('account/privacy/default-public',
        settings.DefaultPrivacySettings.as_view(public=True),
        name='privacy_default_public'),

    path('account/privacy/default-private',
        settings.DefaultPrivacySettings.as_view(public=False),
        name='privacy_default_private'),

    path('account/privacy/<uuid:podcast_id>/public',
        settings.PodcastPrivacySettings.as_view(public=True),
        name='privacy_podcast_public'),

    path('account/privacy/<uuid:podcast_id>/private',
        settings.PodcastPrivacySettings.as_view(public=False),
        name='privacy_podcast_private'),

    path('account/delete',
        settings.delete_account,
        name='delete-account'),

    path('devices/',
        device.overview,
        name='devices'),

    path('devices/create-device',
        device.create,
        name='device-create'),

    path('device/<client-uid:uid>.opml',
        device.opml,
        name='device-opml'),

    path('device/<client-uid:uid>$',
        device.show,
        name='device'),

    path('device/<client-uid:uid>/symbian.opml',
        device.symbian_opml,
        name='device-symbian-opml'),

    path('device/<client-uid:uid>/sync',
        device.sync,
        name='device-sync'),

    path('device/<client-uid:uid>/unsync',
        device.unsync,
        name='device-unsync'),

    path('device/<client-uid:uid>/resync',
        device.resync,
        name='trigger-sync'),

    path('device/<client-uid:uid>/delete',
        device.delete,
        name='device-delete'),

    path('device/<client-uid:uid>/remove',
        device.delete_permanently,
        name='device-delete-permanently'),

    path('device/<client-uid:uid>/undelete',
        device.undelete,
        name='device-undelete'),

    path('device/<client-uid:uid>/edit',
        device.edit,
        name='device-edit'),

    path('device/<client-uid:uid>/update',
        device.update,
        name='device-update'),

    path('device/<client-uid:uid>/upload-opml',
        device.upload_opml,
        name='device-upload-opml'),

    path('register/restore_password',
        user.restore_password,
        name='restore-password'),

    path('login/',
        user.LoginView.as_view(),
        name='login'),

    path('login/google',
        user.GoogleLogin.as_view(),
        name='login-google'),

    path('login/oauth2callback',
        user.GoogleLoginCallback.as_view(),
        name='login-google-callback'),

    path('logout/',
        LogoutView.as_view(),
        kwargs={'next_page': '/'},
        name='logout'),

]
