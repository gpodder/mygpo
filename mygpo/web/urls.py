from django.conf.urls.defaults import *
from registration.views import activate, register
from registration.forms import RegistrationFormUniqueEmail
from django.contrib.auth.views import logout
from django.views.generic.simple import direct_to_template

urlpatterns = patterns('mygpo.web.views',
 url(r'^$',                                                       'home',          name='home'),
    (r'^media/logo/(?P<size>\d+)/(?P<filename>[^/]*)\.jpg$',      'cover_art'),
    (r'^logo/(?P<size>\d+)/(?P<filename>[^/]*)\.jpg$',            'cover_art'),
 url(r'^history/$',                                               'history',       name='history'),
 url(r'^suggestions/$',                                           'suggestions',   name='suggestions'),
 url(r'^suggestions/rate$',                                       'rate_suggestions', name='suggestions-rate'),
 url(r'^suggestions/blacklist/(?P<podcast_id>\d+)$',              'blacklist',     name='suggestions-blacklist'),
 url(r'^tags/',                                                   'mytags',        name='tags'),
 url(r'^online-help',                                              direct_to_template,
       {'template': 'online-help.html'},                                           name='help'),
    (r'^developer/',                                               direct_to_template,
       {'template': 'developer.html'}),
)

urlpatterns += patterns('mygpo.web.views.subscriptions',
 url(r'^subscriptions/$',                                         'show_list',     name='subscriptions'),
 url(r'^download/subscriptions\.opml$',                           'download_all',  name='subscriptions-opml'),
 url(r'^subscriptions/all.opml$',                                 'download_all',  name='subscriptions-download'),
 url(r'^user/(?P<username>[\w-]+)/subscriptions$',                   'for_user',      name='shared-subscriptions'),
 url(r'^user/(?P<username>[\w-]+)/subscriptions\.opml$',             'for_user_opml', name='shared-subscriptions-opml'),
 url(r'^user/(?P<username>[\w-]+)/subscriptions/rss/$',         'subscriptions_feed', name='shared-subscriptions-rss'),
)

urlpatterns += patterns('mygpo.web.views.podcast',
 url(r'^podcast/(?P<pid>\w+)$',                                   'show',          name='podcast'),
 url(r'^subscribe',                                               'subscribe_url', name='subscribe-by-url'),
 url(r'^podcast/(?P<pid>\w+)/subscribe$',                         'subscribe',     name='subscribe'),
 url(r'^podcast/(?P<pid>\w+)/unsubscribe/(?P<device_id>\d+)',     'unsubscribe',   name='unsubscribe'),
 url(r'^podcast/(?P<pid>\w+)/add-tag',                            'add_tag',       name='add-tag'),
 url(r'^podcast/(?P<pid>\w+)/remove-tag',                         'remove_tag',    name='remove-tag'),
)

urlpatterns += patterns('mygpo.web.views.episode',
 url(r'^episode/(?P<id>\d+)$',                                    'episode',       name='episode'),
 url(r'^episode/(?P<id>\d+)/add-chapter$',                        'add_chapter',   name='add-chapter'),
 url(r'^episode/(?P<id>\d+)/remove-chapter/(?P<start>\d+)-(?P<end>\d+)$', 'remove_chapter',name='remove-chapter'),
 url(r'^episode/(?P<id>\d+)/toggle-favorite',                     'toggle_favorite',name='episode-fav'),
 url(r'^favorites/',                                              'list_favorites',name='favorites'),
)

urlpatterns += patterns('mygpo.web.views.settings',
 url(r'^account/$',                                               'account',       name='account'),
 url(r'^account/privacy$',                                        'privacy',       name='privacy'),
 url(r'^account/delete$',                                         'delete_account',name='delete-account'),
 url(r'^share/$',                                                 'share',         name='share'),
)

urlpatterns += patterns('mygpo.web.views.public',
 url(r'^toplist/episodes$',                                       'episode_toplist',            name='episode-toplist'),
 url(r'^gpodder-examples.opml$',                                  'gpodder_example_podcasts',   name='example-opml'),
)

urlpatterns += patterns('mygpo.web.views.device',
 url(r'^devices/$',                                               'overview',                   name='devices'),
 url(r'^devices/create$',                                         'edit',                       name='device-create'),
 url(r'^device/(?P<device_id>\d+)$',                              'show',                       name='device'),
 url(r'^device/(?P<device_id>\d+).opml$',                         'opml',                       name='device-opml'),
 url(r'^device/(?P<device_id>\d+)/symbian.opml$',                 'symbian_opml',               name='device-symbian-opml'),
 url(r'^device/(?P<device_id>\d+)/sync$',                         'sync',                       name='device-sync'),
 url(r'^device/(?P<device_id>\d+)/unsync$',                       'unsync',                     name='device-unsync'),
 url(r'^device/(?P<device_id>\d+)/delete$',                       'delete',                     name='device-delete'),
 url(r'^device/(?P<device_id>\d+)/remove$',                       'delete_permanently',         name='device-delete-permanently'),
 url(r'^device/(?P<device_id>\d+)/undelete$',                     'undelete',                   name='device-undelete'),
 url(r'^device/(?P<device_id>\d+)/history$',                      'history',                    name='device-history'),
 url(r'^device/(?P<device_id>\d+)/edit$',                         'edit',                       name='device-edit'),
 url(r'^device/(?P<device_id>\d+)/upload-opml$',                  'upload_opml',                name='device-upload-opml'),
)

urlpatterns += patterns('mygpo.web.views.users',
 url(r'^login/$',                                                 'login_user',                 name='login'),
 url(r'^logout/$',                                                 logout, {'next_page': '/'},  name='logout'),
 url(r'^migrate/$',                                               'migrate_user',               name='migrate-user'),
 url(r'^register/resend-activation$',                             'resend_activation',          name='resend-activation'),
 url(r'^register/restore_password$',                              'restore_password',           name='restore-password'),
 url(r'^register/$',                                               register,
            {'backend': 'registration.backends.default.DefaultBackend',
             'form_class': RegistrationFormUniqueEmail},                                        name='register'),
    (r'^registration_complete/$',                                  direct_to_template,
            {'template': 'registration/registration_complete.html'}),
    (r'^activate/(?P<activation_key>\w+)$',                        activate,
            {'backend': 'registration.backends.default.DefaultBackend'}),
)

