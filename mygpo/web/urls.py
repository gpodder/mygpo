from django.conf.urls import url
from django.contrib.auth.views import logout
from django.views.generic.base import TemplateView, RedirectView

from mygpo.web.logo import CoverArt

from . import views
from .views import subscriptions, podcast, episode, settings, device, users

urlpatterns = [
 url(r'^$',                                                       views.home,          name='home'),
 url(r'^logo/(?P<size>\d+)/(?P<prefix>.{3})/(?P<filename>[^/]*)$', CoverArt.as_view(), name='logo'),
 url(r'^tags/',                                                   views.mytags,        name='tags'),

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

 url(r'^user/(?P<username>[\w.+-]+)/subscriptions$',                   subscriptions.for_user,      name='shared-subscriptions'),
 url(r'^user/(?P<username>[\w.+-]+)/subscriptions\.opml$',             subscriptions.for_user_opml, name='shared-subscriptions-opml'),

 url(r'^subscribe',                                               podcast.subscribe_url, name='subscribe-by-url'),

 # Podcast Views with UUIDs
 url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/?$',
     podcast.show_id,
     name='podcast-id'),

 url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/subscribe$',
     podcast.subscribe_id,
     name='subscribe-id'),

 url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/subscribe/\+all$',
     podcast.subscribe_all_id,
     name='subscribe-all-id'),

 url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/unsubscribe/(?P<device_uid>[\w.-]+)',
     podcast.unsubscribe_id,
     name='unsubscribe-id'),

 url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/unsubscribe/\+all$',
     podcast.unsubscribe_all_id,
     name='unsubscribe-all-id'),

 url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/add-tag',
     podcast.add_tag_id,
     name='add-tag-id'),

 url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/remove-tag',
     podcast.remove_tag_id,
     name='remove-tag-id'),

 url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/set-public',
     podcast.set_public_id,
     name='podcast-public-id',
     kwargs={'public': True}),

 url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/set-private',
     podcast.set_public_id,
     name='podcast-private-id',
     kwargs={'public': False}),

 url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/-episodes',
     podcast.all_episodes_id,
     name='podcast-all-episodes-id'),

 url(r'^podcast/(?P<podcast_id>[0-9a-f]{32})/-flattr',
     podcast.flattr_podcast_id,
     name='podcast-flattr-id'),


 # Podcast Views with Slugs
 url(r'^podcast/(?P<slug>[\w-]+)/?$',
     podcast.show_slug,
     name='podcast-slug'),

 url(r'^podcast/(?P<slug>[\w-]+)/subscribe$',
     podcast.subscribe_slug,
     name='subscribe-slug'),

 url(r'^podcast/(?P<slug>[\w-]+)/subscribe/\+all$',
     podcast.subscribe_all_slug,
     name='subscribe-all-slug'),

 url(r'^podcast/(?P<slug>[\w-]+)/unsubscribe/(?P<device_uid>[\w.-]+)',
     podcast.unsubscribe_slug,
     name='unsubscribe-slug'),

 url(r'^podcast/(?P<slug>[\w-]+)/unsubscribe/\+all$',
     podcast.unsubscribe_all_slug,
     name='unsubscribe-all-slug'),

 url(r'^podcast/(?P<slug>[\w-]+)/add-tag',
     podcast.add_tag_slug,
     name='add-tag-slug'),

 url(r'^podcast/(?P<slug>[\w-]+)/remove-tag',
     podcast.remove_tag_slug,
     name='remove-tag-slug'),

 url(r'^podcast/(?P<slug>[\w-]+)/set-public',
     podcast.set_public_slug,
     name='podcast-public-slug',
     kwargs={'public': True}),

 url(r'^podcast/(?P<slug>[\w-]+)/set-private',
     podcast.set_public_slug,
     name='podcast-private-slug',
     kwargs={'public': False}),

 url(r'^podcast/(?P<slug>[\w-]+)/-episodes',
     podcast.all_episodes_slug,
     name='podcast-all-episodes-slug'),

 url(r'^podcast/(?P<slug>[\w-]+)/-flattr',
     podcast.flattr_podcast_slug,
     name='podcast-flattr-slug'),

 url(r'^favorites/$',
     episode.list_favorites,
     name='favorites'),

 # Episodes for UUIDs
 url(r'^podcast/(?P<p_id>[0-9a-f]{32})/(?P<e_id>[0-9a-f]{32})$',
     episode.show_id,
     name='episode-id'),

 url(r'^podcast/(?P<p_id>[0-9a-f]{32})/(?P<e_id>[0-9a-f]{32})/toggle-favorite',
     episode.toggle_favorite_id,
     name='episode-fav-id'),

 url(r'^podcast/(?P<p_id>[0-9a-f]{32})/(?P<e_id>[0-9a-f]{32})/add-action',
     episode.add_action_id,
     name='add-episode-action-id'),

 url(r'^podcast/(?P<p_id>[0-9a-f]{32})/(?P<e_id>[0-9a-f]{32})/-flattr',
     episode.flattr_episode_id,
     name='flattr-episode-id'),

 url(r'^podcast/(?P<p_id>[0-9a-f]{32})/(?P<e_id>[0-9a-f]{32})/\+history',
     episode.episode_history_id,
     name='episode-history-id'),


 # Episodes for Slugs
 url(r'^podcast/(?P<p_slug>[\w-]+)/(?P<e_slug>[\w-]+)$',
     episode.show_slug,
     name='episode-slug'),

 url(r'^podcast/(?P<p_slug>[\w-]+)/(?P<e_slug>[\w-]+)/toggle-favorite',
     episode.toggle_favorite_slug,
     name='episode-fav-slug'),

 url(r'^podcast/(?P<p_slug>[\w-]+)/(?P<e_slug>[\w-]+)/add-action',
     episode.add_action_slug,
     name='add-episode-action-slug'),

 url(r'^podcast/(?P<p_slug>[\w-]+)/(?P<e_slug>[\w-]+)/-flattr',
     episode.flattr_episode_slug,  name='flattr-episode-slug'),

 url(r'^podcast/(?P<p_slug>[\w-]+)/(?P<e_slug>[\w-]+)/\+history',
     episode.episode_history_slug,
     name='episode-history-slug'),

 url(r'^account/$',                                               settings.account,       name='account'),
 url(r'^account/privacy$',                                        settings.privacy,       name='privacy'),

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

 url(r'^account/delete$',                                         settings.delete_account,name='delete-account'),

 url(r'^devices/$',                                            device.overview,                   name='devices'),
 url(r'^devices/create-device$',                               device.create,                     name='device-create'),
 url(r'^device/(?P<uid>[\w.-]+)\.opml$',                       device.opml,                       name='device-opml'),
 url(r'^device/(?P<uid>[\w.-]+)$',                             device.show,                       name='device'),
 url(r'^device/(?P<uid>[\w.-]+)/symbian.opml$',                device.symbian_opml,               name='device-symbian-opml'),
 url(r'^device/(?P<uid>[\w.-]+)/sync$',                        device.sync,                       name='device-sync'),
 url(r'^device/(?P<uid>[\w.-]+)/unsync$',                      device.unsync,                     name='device-unsync'),
 url(r'^device/(?P<uid>[\w.-]+)/resync$',                      device.resync,                     name='trigger-sync'),
 url(r'^device/(?P<uid>[\w.-]+)/delete$',                      device.delete,                     name='device-delete'),
 url(r'^device/(?P<uid>[\w.-]+)/remove$',                      device.delete_permanently,         name='device-delete-permanently'),
 url(r'^device/(?P<uid>[\w.-]+)/undelete$',                    device.undelete,                   name='device-undelete'),
 url(r'^device/(?P<uid>[\w.-]+)/edit$',                        device.edit,                       name='device-edit'),
 url(r'^device/(?P<uid>[\w.-]+)/update$',                      device.update,                     name='device-update'),
 url(r'^device/(?P<uid>[\w.-]+)/upload-opml$',                 device.upload_opml,                name='device-upload-opml'),


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

 url(r'^logout/$',                                                 logout, {'next_page': '/'},  name='logout'),

]
