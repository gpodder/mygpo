from django.conf.urls import *
from django.contrib.auth.views import logout
from django.views.generic.base import TemplateView, RedirectView

from mygpo.web.logo import CoverArt


urlpatterns = patterns('mygpo.web.views',
 url(r'^$',                                                       'home',          name='home'),
 url(r'^logo/(?P<size>\d+)/(?P<prefix>.{3})/(?P<filename>[^/]*)$', CoverArt.as_view(), name='logo'),
 url(r'^tags/',                                                   'mytags',        name='tags'),

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

)

urlpatterns += patterns('mygpo.web.views.subscriptions',
 url(r'^user/(?P<username>[\w.+-]+)/subscriptions$',                   'for_user',      name='shared-subscriptions'),
 url(r'^user/(?P<username>[\w.+-]+)/subscriptions\.opml$',             'for_user_opml', name='shared-subscriptions-opml'),
)

urlpatterns += patterns('mygpo.web.views.podcast',
 url(r'^subscribe',                                               'subscribe_url', name='subscribe-by-url'),

 # Podcast Views with UUIDs
 url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/?$',
     'show_id',
     name='podcast-id'),

 url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/subscribe$',
     'subscribe_id',
     name='subscribe-id'),

 url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/subscribe/\+all$',
     'subscribe_all_id',
     name='subscribe-all-id'),

 url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/unsubscribe/(?P<device_uid>[\w.-]+)',
     'unsubscribe_id',
     name='unsubscribe-id'),

 url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/unsubscribe/\+all$',
     'unsubscribe_all_id',
     name='unsubscribe-all-id'),

 url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/add-tag',
     'add_tag_id',
     name='add-tag-id'),

 url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/remove-tag',
     'remove_tag_id',
     name='remove-tag-id'),

 url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/set-public',
     'set_public_id',
     name='podcast-public-id',
     kwargs={'public': True}),

 url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/set-private',
     'set_public_id',
     name='podcast-private-id',
     kwargs={'public': False}),

 url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/-episodes',
     'all_episodes_id',
     name='podcast-all-episodes-id'),

 url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/-flattr',
     'flattr_podcast_id',
     name='podcast-flattr-id'),


 # Podcast Views with Slugs
 url(r'^podcast/(?P<slug>[\w-]+)/?$',
     'show_slug',
     name='podcast-slug'),

 url(r'^podcast/(?P<slug>[\w-]+)/subscribe$',
     'subscribe_slug',
     name='subscribe-slug'),

 url(r'^podcast/(?P<slug>[\w-]+)/subscribe/\+all$',
     'subscribe_all_slug',
     name='subscribe-all-slug'),

 url(r'^podcast/(?P<slug>[\w-]+)/unsubscribe/(?P<device_uid>[\w.-]+)',
     'unsubscribe_slug',
     name='unsubscribe-slug'),

 url(r'^podcast/(?P<slug>[\w-]+)/unsubscribe/\+all$',
     'unsubscribe_all_slug',
     name='unsubscribe-all-slug'),

 url(r'^podcast/(?P<slug>[\w-]+)/add-tag',
     'add_tag_slug',
     name='add-tag-slug'),

 url(r'^podcast/(?P<slug>[\w-]+)/remove-tag',
     'remove_tag_slug',
     name='remove-tag-slug'),

 url(r'^podcast/(?P<slug>[\w-]+)/set-public',
     'set_public_slug',
     name='podcast-public-slug',
     kwargs={'public': True}),

 url(r'^podcast/(?P<slug>[\w-]+)/set-private',
     'set_public_slug',
     name='podcast-private-slug',
     kwargs={'public': False}),

 url(r'^podcast/(?P<slug>[\w-]+)/-episodes',
     'all_episodes_slug',
     name='podcast-all-episodes-slug'),

 url(r'^podcast/(?P<slug>[\w-]+)/-flattr',
     'flattr_podcast_slug',
     name='podcast-flattr-slug'),
 )


urlpatterns += patterns('mygpo.web.views.episode',

 url(r'^favorites/$',
     'list_favorites',
     name='favorites'),

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
         FlattrTokenView, FlattrLogout, AccountRemoveGoogle

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

 url(r'^account/delete$',                                         'delete_account',name='delete-account'),
)

urlpatterns += patterns('mygpo.web.views.device',
 url(r'^devices/$',                                            'overview',                   name='devices'),
 url(r'^devices/create-device$',                               'create',                     name='device-create'),
 url(r'^device/(?P<uid>[\w.-]+)\.opml$',                        'opml',                       name='device-opml'),
 url(r'^device/(?P<uid>[\w.-]+)$',                              'show',                       name='device'),
 url(r'^device/(?P<uid>[\w.-]+)/symbian.opml$',                 'symbian_opml',               name='device-symbian-opml'),
 url(r'^device/(?P<uid>[\w.-]+)/sync$',                         'sync',                       name='device-sync'),
 url(r'^device/(?P<uid>[\w.-]+)/unsync$',                       'unsync',                     name='device-unsync'),
 url(r'^device/(?P<uid>[\w.-]+)/resync$',                       'resync',                     name='trigger-sync'),
 url(r'^device/(?P<uid>[\w.-]+)/delete$',                       'delete',                     name='device-delete'),
 url(r'^device/(?P<uid>[\w.-]+)/remove$',                       'delete_permanently',         name='device-delete-permanently'),
 url(r'^device/(?P<uid>[\w.-]+)/undelete$',                     'undelete',                   name='device-undelete'),
 url(r'^device/(?P<uid>[\w.-]+)/edit$',                         'edit',                       name='device-edit'),
 url(r'^device/(?P<uid>[\w.-]+)/update$',                       'update',                     name='device-update'),
 url(r'^device/(?P<uid>[\w.-]+)/upload-opml$',                  'upload_opml',                name='device-upload-opml'),
)


from mygpo.web.views.users import LoginView, GoogleLogin, GoogleLoginCallback

urlpatterns += patterns('mygpo.web.views.users',

 url(r'^register/restore_password$',
    'restore_password',
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
