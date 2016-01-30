from django.conf.urls import url
from django.contrib.auth.views import logout
from django.views.generic.base import TemplateView, RedirectView

from mygpo.web.logo import CoverArt

from . import views
from .views import settings, device, users


urlpatterns = [

    url(r'^$',
        views.home,
        name='home'),

    url(r'^logo/(?P<size>\d+)/(?P<prefix>.{3})/(?P<filename>[^/]*)$',
        CoverArt.as_view(),
        name='logo'),

    url(r'^tags/',
        views.mytags,
        name='tags'),

    url(r'^online-help',
        RedirectView.as_view(
            url='http://gpoddernet.readthedocs.org/en/latest/user/index.html',
            permanent=False,
        ),
        name='help'),

    url(r'^developer/',
        TemplateView.as_view(template_name='developer.html')),

    url(r'^contribute/',
        TemplateView.as_view(template_name='contribute.html'),
        name='contribute'),

    url(r'^privacy/',
        TemplateView.as_view(template_name='privacy_policy.html'),
        name='privacy-policy'),

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

    url(r'^account/flattr$',
        settings.FlattrSettingsView.as_view(),
        name='flattr-settings'),

    url(r'^account/flattr/token$',
        settings.FlattrTokenView.as_view(),
        name='flattr-token'),

    url(r'^account/flattr/logout$',
        settings.FlattrLogout.as_view(),
        name='flattr-logout'),

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
        users.restore_password,
        name='restore-password'),

    url(r'^login/$',
        users.LoginView.as_view(),
        name='login'),

    url(r'^login/google$',
        users.GoogleLogin.as_view(),
        name='login-google'),

    url(r'^login/oauth2callback$',
        users.GoogleLoginCallback.as_view(),
        name='login-google-callback'),

    url(r'^logout/$',
        logout,
        kwargs={'next_page': '/'},
        name='logout'),

]
