from django.conf.urls.defaults import *
from django.contrib.auth.views import logout
from django.views.generic.simple import direct_to_template

from django_couchdb_utils.registration.views import activate, register
from django_couchdb_utils.registration.forms import RegistrationFormUniqueEmail

from mygpo.web.logo import CoverArt


urlpatterns = patterns('mygpo.web.views',
 url(r'^$',                                                       'home',          name='home'),
 url(r'^logo/(?P<size>\d+)/(?P<prefix>.{3})/(?P<filename>[^/]*)\.jpg$',      CoverArt.as_view(),     name='logo'),
 url(r'^history/$',                                               'history',       name='history'),
 url(r'^suggestions/$',                                           'suggestions',   name='suggestions'),
 url(r'^suggestions/rate$',                                       'rate_suggestions', name='suggestions-rate'),
 url(r'^suggestions/blacklist/(?P<podcast_id>\d+)$',              'blacklist',     name='suggestions-blacklist'),
 url(r'^tags/',                                                   'mytags',        name='tags'),
 url(r'^online-help',                                              direct_to_template,
       {'template': 'online-help.html'},                                           name='help'),
    (r'^developer/',                                               direct_to_template,
       {'template': 'developer.html'}),
 url(r'^contribute/',                                              direct_to_template,
       {'template': 'contribute.html'}),
 url(r'^privacy/',                                              direct_to_template,
       {'template': 'privacy_policy.html'}, name='privacy-policy'),

)

urlpatterns += patterns('mygpo.web.views.subscriptions',
 url(r'^subscriptions/$',                                         'show_list',     name='subscriptions'),
 url(r'^download/subscriptions\.opml$',                           'download_all',  name='subscriptions-opml'),
 url(r'^subscriptions/all.opml$',                                 'download_all',  name='subscriptions-download'),
 url(r'^user/(?P<username>[\w.-]+)/subscriptions$',                   'for_user',      name='shared-subscriptions'),
 url(r'^user/(?P<username>[\w.-]+)/subscriptions\.opml$',             'for_user_opml', name='shared-subscriptions-opml'),
 url(r'^user/(?P<username>[\w.-]+)/subscriptions/rss/$',         'subscriptions_feed', name='shared-subscriptions-rss'),
)

urlpatterns += patterns('mygpo.web.views.podcast',
 url(r'^subscribe',                                               'subscribe_url', name='subscribe-by-url'),

 url(r'^podcast/(?P<pid>\d+)$',                                   'show_oldid',          name='podcast'),
 url(r'^podcast/(?P<pid>\d+)/subscribe$',                         'subscribe_oldid',     name='subscribe'),
 url(r'^podcast/(?P<pid>\d+)/unsubscribe/(?P<device_uid>[\w.-]+)',     'unsubscribe_oldid',   name='unsubscribe'),
 url(r'^podcast/(?P<pid>\d+)/add-tag',                            'add_tag_oldid',       name='add-tag'),
 url(r'^podcast/(?P<pid>\d+)/remove-tag',                         'remove_tag_oldid',    name='remove-tag'),
 url(r'^podcast/(?P<pid>\d+)/set-public',                         'set_public_oldid',    name='podcast-public',  kwargs={'public': True}),
 url(r'^podcast/(?P<pid>\d+)/set-private',                        'set_public_oldid',    name='podcast-private', kwargs={'public': False}),

 url(r'^podcast/(?P<slug_id>[\w-]+)/?$',                             'show_slug_id',        name='podcast-slug-id'),
 url(r'^podcast/(?P<slug_id>[\w-]+)/subscribe$',                     'subscribe_slug_id',   name='subscribe-slug-id'),
 url(r'^podcast/(?P<slug_id>[\w-]+)/unsubscribe/(?P<device_uid>[\w.-]+)', 'unsubscribe_slug_id', name='unsubscribe-slug-id'),
 url(r'^podcast/(?P<slug_id>[\w-]+)/add-tag',                        'add_tag_slug_id',     name='add-tag-slug-id'),
 url(r'^podcast/(?P<slug_id>[\w-]+)/remove-tag',                     'remove_tag_slug_id',  name='remove-tag-slug-id'),
 url(r'^podcast/(?P<slug_id>[\w-]+)/set-public',                     'set_public_slug_id',    name='podcast-public-slug-id',  kwargs={'public': True}),
 url(r'^podcast/(?P<slug_id>[\w-]+)/set-private',                    'set_public_slug_id',    name='podcast-private-slug-id', kwargs={'public': False}),
 )


urlpatterns += patterns('mygpo.web.views.episode',
 url(r'^favorites/',                                              'list_favorites',name='favorites'),

 url(r'^episode/(?P<id>\d+)$',                                    'show_oldid',           name='episode'),
 url(r'^episode/(?P<id>\d+)/add-chapter$',                        'add_chapter_oldid',   name='add-chapter'),
 url(r'^episode/(?P<id>\d+)/remove-chapter/(?P<start>\d+)-(?P<end>\d+)$', 'remove_chapter_oldid',name='remove-chapter'),
 url(r'^episode/(?P<id>\d+)/toggle-favorite',                     'toggle_favorite_oldid',name='episode-fav'),
 url(r'^episode/(?P<id>\d+)/add-action',                          'add_action_oldid',    name='add-episode-action'),

 url(r'^podcast/(?P<p_slug_id>[\w-]+)/(?P<e_slug_id>[\w-]+)$',                'show_slug_id',            name='episode-slug-id'),
 url(r'^episode/(?P<p_slug_id>[\w-]+)/(?P<e_slug_id>[\w-]+)/add-chapter$',    'add_chapter_slug_id',     name='add-chapter-slug-id'),
 url(r'^episode/(?P<p_slug_id>[\w-]+)/(?P<e_slug_id>[\w-]+)/remove-chapter/(?P<start>\d+)-(?P<end>\d+)$',
                                                                              'remove_chapter',          name='remove-chapter'),
 url(r'^episode/(?P<p_slug_id>[\w-]+)/(?P<e_slug_id>[\w-]+)/toggle-favorite', 'toggle_favorite_slug_id', name='episode-fav-slug-id'),
 url(r'^episode/(?P<p_slug_id>[\w-]+)/(?P<e_slug_id>[\w-]+)/add-action',      'add_action_slug_id',      name='add-episode-action-slug-id'),
)

urlpatterns += patterns('mygpo.web.views.settings',
 url(r'^account/$',                                               'account',       name='account'),
 url(r'^account/privacy$',                                        'privacy',       name='privacy'),
 url(r'^account/delete$',                                         'delete_account',name='delete-account'),
)

urlpatterns += patterns('mygpo.web.views.device',
 url(r'^devices/$',                                            'overview',                   name='devices'),
 url(r'^devices/create$',                                      'edit_new',                   name='device-edit-new'),
 url(r'^devices/create-device$',                               'create',                     name='device-create'),
 url(r'^device/(?P<uid>[\w.-]+)\.opml$',                        'opml',                       name='device-opml'),
 url(r'^device/(?P<uid>[\w.-]+)$',                              'show',                       name='device'),
 url(r'^device/(?P<uid>[\w.-]+)/symbian.opml$',                 'symbian_opml',               name='device-symbian-opml'),
 url(r'^device/(?P<uid>[\w.-]+)/sync$',                         'sync',                       name='device-sync'),
 url(r'^device/(?P<uid>[\w.-]+)/unsync$',                       'unsync',                     name='device-unsync'),
 url(r'^device/(?P<uid>[\w.-]+)/delete$',                       'delete',                     name='device-delete'),
 url(r'^device/(?P<uid>[\w.-]+)/remove$',                       'delete_permanently',         name='device-delete-permanently'),
 url(r'^device/(?P<uid>[\w.-]+)/undelete$',                     'undelete',                   name='device-undelete'),
 url(r'^device/(?P<uid>[\w.-]+)/history$',                      'history',                    name='device-history'),
 url(r'^device/(?P<uid>[\w.-]+)/edit$',                         'edit',                       name='device-edit'),
 url(r'^device/(?P<uid>[\w.-]+)/update$',                       'update',                     name='device-update'),
 url(r'^device/(?P<uid>[\w.-]+)/upload-opml$',                  'upload_opml',                name='device-upload-opml'),
)

urlpatterns += patterns('mygpo.web.views.users',
 url(r'^login/$',                                                 'login_user',                 name='login'),
 url(r'^logout/$',                                                 logout, {'next_page': '/'},  name='logout'),
 url(r'^register/resend-activation$',                             'resend_activation',          name='resend-activation'),
 url(r'^register/restore_password$',                              'restore_password',           name='restore-password'),
 url(r'^register/$',                                               register,
            {'backend': 'django_couchdb_utils.registration.backends.default.DefaultBackend',
             'form_class': RegistrationFormUniqueEmail},                                        name='register'),
    (r'^registration_complete/$',                                  direct_to_template,
            {'template': 'registration/registration_complete.html'}),
    (r'^activate/(?P<activation_key>\w+)$',                        activate,
            {'backend': 'django_couchdb_utils.registration.backends.default.DefaultBackend'}),
)

