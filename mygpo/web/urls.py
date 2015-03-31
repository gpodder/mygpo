from django.conf.urls import *
from django.contrib.auth.views import logout
from django.views.generic.base import TemplateView, RedirectView

from mygpo.web.views import MyTags
from mygpo.web.logo import CoverArt


urlpatterns = patterns('mygpo.web.views',
 url(r'^$',                                                       'dashboard',          name='home'),
 url(r'^logo/(?P<size>\d+)/(?P<prefix>.{3})/(?P<filename>[^/]*)$', CoverArt.as_view(), name='logo'),
 url(r'^tags/',
     MyTags.as_view(),
     name='tags'),

 url(r'^online-help',
     RedirectView.as_view(
         url='http://gpoddernet.readthedocs.org/en/latest/user/index.html'),
     name='help'),

 url(r'^developer/',
     TemplateView.as_view(template_name='developer.html')),

 url(r'^contribute/',
     TemplateView.as_view(template_name='contribute.html'),
     name='contribute'),

 url(r'^privacy/',
     TemplateView.as_view(template_name='privacy_policy.html'),
     name='privacy-policy'),

)

urlpatterns += patterns('mygpo.web.views.episode',

 # Episodes for UUIDs
 url(r'^podcast/(?P<p_id>[0-9a-f]{32})/(?P<e_id>[0-9a-f]{32})$',
     'show_id',
     name='episode-id'),

 url(r'^podcast/(?P<p_id>[0-9a-f]{32})/(?P<e_id>[0-9a-f]{32})/toggle-favorite',
     'toggle_favorite_id',
     name='episode-fav-id'),

 url(r'^podcast/(?P<p_id>[0-9a-f]{32})/(?P<e_id>[0-9a-f]{32})/add-action',
     'add_action_id',
     name='add-episode-action-id'),

 url(r'^podcast/(?P<p_id>[0-9a-f]{32})/(?P<e_id>[0-9a-f]{32})/-flattr',
     'flattr_episode_id',
     name='flattr-episode-id'),

 url(r'^podcast/(?P<p_id>[0-9a-f]{32})/(?P<e_id>[0-9a-f]{32})/\+history',
     'episode_history_id',
     name='episode-history-id'),


 # Episodes for Slugs
 url(r'^podcast/(?P<p_slug>[\w-]+)/(?P<e_slug>[\w-]+)$',
     'show_slug',
     name='episode-slug'),

 url(r'^podcast/(?P<p_slug>[\w-]+)/(?P<e_slug>[\w-]+)/toggle-favorite',
     'toggle_favorite_slug',
     name='episode-fav-slug'),

 url(r'^podcast/(?P<p_slug>[\w-]+)/(?P<e_slug>[\w-]+)/add-action',
     'add_action_slug',
     name='add-episode-action-slug'),

 url(r'^podcast/(?P<p_slug>[\w-]+)/(?P<e_slug>[\w-]+)/-flattr',
     'flattr_episode_slug',  name='flattr-episode-slug'),

 url(r'^podcast/(?P<p_slug>[\w-]+)/(?P<e_slug>[\w-]+)/\+history',
     'episode_history_slug',
     name='episode-history-slug'),
)

from mygpo.web.views.settings import DefaultPrivacySettings, \
         PodcastPrivacySettings, ProfileView, FlattrSettingsView, \
         FlattrTokenView, FlattrLogout, AccountRemoveGoogle, DeleteAccount

urlpatterns += patterns('mygpo.web.views.settings',
 url(r'^account/$',                                               'account',       name='account'),
 url(r'^account/privacy$',                                        'privacy',       name='privacy'),

 url(r'^account/profile$',
     ProfileView.as_view(),
     name='profile'),

 url(r'^account/google/remove$',
     AccountRemoveGoogle.as_view(),
     name='account-google-remove'),

 url(r'^account/flattr$',
     FlattrSettingsView.as_view(),
     name='flattr-settings'),

 url(r'^account/flattr/token$',
     FlattrTokenView.as_view(),
     name='flattr-token'),

 url(r'^account/flattr/logout$',
     FlattrLogout.as_view(),
     name='flattr-logout'),

 url(r'^account/privacy/default-public$',
     DefaultPrivacySettings.as_view(public=True),
     name='privacy_default_public'),

 url(r'^account/privacy/default-private$',
     DefaultPrivacySettings.as_view(public=False),
     name='privacy_default_private'),

 url(r'^account/privacy/(?P<podcast_id>[\w]+)/public$',
     PodcastPrivacySettings.as_view(public=True),
     name='privacy_podcast_public'),

 url(r'^account/privacy/(?P<podcast_id>[\w]+)/private$',
     PodcastPrivacySettings.as_view(public=False),
     name='privacy_podcast_private'),

 url(r'^account/delete$',
     DeleteAccount.as_view(),
     name='delete-account'),
)

from mygpo.web.views.device import ClientList, ClientDetails

urlpatterns += patterns('mygpo.web.views.device',
 url(r'^devices/$',
     ClientList.as_view(),
     name='devices'),

 url(r'^devices/create-device$',                               'create',                     name='device-create'),
 url(r'^device/(?P<uid>[\w.-]+)\.opml$',                        'opml',                       name='device-opml'),
 url(r'^device/(?P<uid>[\w.-]+)$',
     ClientDetails.as_view(),
     name='device'),

 url(r'^device/(?P<uid>[\w.-]+)/symbian.opml$',                 'symbian_opml',               name='device-symbian-opml'),
 url(r'^device/(?P<uid>[\w.-]+)/sync$',                         'sync',                       name='device-sync'),
 url(r'^device/(?P<uid>[\w.-]+)/unsync$',                       'unsync',                     name='device-unsync'),
 url(r'^device/(?P<uid>[\w.-]+)/resync$',                       'resync',                     name='trigger-sync'),
 url(r'^device/(?P<uid>[\w.-]+)/delete$',                       'delete',                     name='device-delete'),
 url(r'^device/(?P<uid>[\w.-]+)/remove$',                       'delete_permanently',         name='device-delete-permanently'),
 url(r'^device/(?P<uid>[\w.-]+)/undelete$',                     'undelete',                   name='device-undelete'),
 url(r'^device/(?P<uid>[\w.-]+)/update$',                       'update',                     name='device-update'),
 url(r'^device/(?P<uid>[\w.-]+)/upload-opml$',                  'upload_opml',                name='device-upload-opml'),
)


from mygpo.web.views.users import LoginView, GoogleLogin, GoogleLoginCallback, RestorePassword

urlpatterns += patterns('mygpo.web.views.users',

 url(r'^register/restore_password$',
    RestorePassword.as_view(),
    name='restore-password'),

 url(r'^login/$',
    LoginView.as_view(),
    name='login'),

 url(r'^login/google$',
     GoogleLogin.as_view(),
     name='login-google'),

 url(r'^login/oauth2callback$',
     GoogleLoginCallback.as_view(),
     name='login-google-callback'),

 url(r'^logout/$',                                                 logout, {'next_page': '/'},  name='logout'),
)
