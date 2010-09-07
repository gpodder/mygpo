from django.conf.urls.defaults import *
from registration.views import activate, register
from registration.forms import RegistrationFormUniqueEmail
from registration.backends import default
from django.contrib.auth.views import logout
from django.views.generic.simple import direct_to_template

urlpatterns = patterns('mygpo.web.views',
    (r'^$',                                                       'home'),
    (r'^media/logo/(?P<size>\d+)/(?P<filename>[^/]*)\.jpg$',      'cover_art'),
    (r'^logo/(?P<size>\d+)/(?P<filename>[^/]*)\.jpg$',            'cover_art'),
    (r'^history/$',                                               'history'),
    (r'^suggestions/$',                                           'suggestions'),
    (r'^tags/',                                                   'mytags'),
    (r'^online-help',                                              direct_to_template, {'template': 'online-help.html'}),
)

urlpatterns += patterns('mygpo.web.views.subscriptions',
    (r'^subscriptions/$',                                         'list'),
    (r'^download/subscriptions\.opml$',                           'download_all'),
    (r'^subscriptions/all.opml$',                                 'download_all'),
    (r'^user/(?P<username>\w+)/subscriptions$',                   'for_user'),
    (r'^user/(?P<username>\w+)/subscriptions\.opml$',             'for_user_opml'),
)

urlpatterns += patterns('mygpo.web.views.podcast',
    (r'^podcast/(?P<pid>\w+)$',                                   'show'),
    (r'^subscribe',                                               'subscribe_url'),
    (r'^podcast/(?P<pid>\w+)/subscribe$',                         'subscribe'),
    (r'^podcast/(?P<pid>\w+)/unsubscribe/(?P<device_id>\d+)',     'unsubscribe'),
    (r'^podcast/(?P<pid>\w+)/add-tag',                            'add_tag'),
    (r'^podcast/(?P<pid>\w+)/remove-tag',                         'remove_tag'),
)

urlpatterns += patterns('mygpo.web.views.episode',
    (r'^episode/(?P<id>\d+)$',                                    'episode'),
    (r'^episode/(?P<id>\d+)/add-chapter$',                        'add_chapter'),
    (r'^episode/(?P<id>\d+)/remove-chapter/(?P<chapter_id>\d+)$', 'remove_chapter'),
    (r'^episode/(?P<id>\d+)/toggle-favorite',                     'toggle_favorite'),
    (r'^favorites/',                                              'list_favorites'),
)

urlpatterns += patterns('mygpo.web.views.settings',
    (r'^account/$',                                               'account'),
    (r'^account/privacy$',                                        'privacy'),
    (r'^account/delete$',                                         'delete_account'),
    (r'^share/$',                                                 'share'),
)

urlpatterns += patterns('mygpo.web.views.public',
    (r'^directory/$',                                             'browse'),
    (r'^directory/(?P<category>[^/]+)$',                          'category'),
    (r'^toplist/$',                                               'toplist'),
    (r'^toplist/episodes$',                                       'episode_toplist'),
    (r'^gpodder-examples.opml$',                                  'gpodder_example_podcasts'),
)

urlpatterns += patterns('mygpo.web.views.device',
    (r'^devices/$',                                               'overview'),
    (r'^device/(?P<device_id>\d+)$',                              'show'),
    (r'^device/(?P<device_id>\d+).opml$',                         'opml'),
    (r'^device/(?P<device_id>\d+)/sync$',                         'sync'),
    (r'^device/(?P<device_id>\d+)/unsync$',                       'unsync'),
    (r'^device/(?P<device_id>\d+)/delete$',                       'delete'),
    (r'^device/(?P<device_id>\d+)/remove$',                       'delete_permanently'),
    (r'^device/(?P<device_id>\d+)/undelete$',                     'undelete'),
    (r'^device/(?P<device_id>\d+)/history$',                      'history'),
    (r'^device/(?P<device_id>\d+)/edit$',                         'edit'),
)

urlpatterns += patterns('mygpo.web.views.users',
    (r'^login/$',                                                 'login_user'),
    (r'^logout/$',                                                 logout, {'next_page': '/'}),
    (r'^migrate/$',                                               'migrate_user'),
    (r'^register/resend-activation$',                             'resend_activation'),
    (r'^register/restore_password$',                              'restore_password'),
    (r'^register/$',                                               register,
            {'backend': 'registration.backends.default.DefaultBackend',
             'form_class': RegistrationFormUniqueEmail}),
    (r'^registration_complete/$',                                  direct_to_template,
            {'template': 'registration/registration_complete.html'}),
    (r'^activate/(?P<activation_key>\w+)$',                        activate,
            {'backend': 'registration.backends.default.DefaultBackend'}),
)

