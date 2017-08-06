import re
import sys
import os.path
import dj_database_url


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_bool(name, default):
    return os.getenv(name, str(default)).lower() == 'true'


def get_intOrNone(name, default):
    """ Parses the env variable, accepts ints and literal None"""
    value = os.getenv(name, str(default))
    if value.lower() == 'none':
        return None
    return int(value)


DEBUG = get_bool('DEBUG', False)

ADMINS = re.findall(r'\s*([^<]+) <([^>]+)>\s*', os.getenv('ADMINS', ''))

MANAGERS = ADMINS

DATABASES = {
    'default': dj_database_url.config(
        default='postgres://mygpo:mygpo@localhost/mygpo'),
}


_cache_used = bool(os.getenv('CACHE_BACKEND', False))

if _cache_used:
    CACHES = {}
    CACHES['default'] = {
        'BACKEND': os.getenv(
            'CACHE_BACKEND',
            'django.core.cache.backends.memcached.MemcachedCache'),
        'LOCATION': os.getenv('CACHE_LOCATION'),
    }


# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'UTC'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

STATIC_ROOT = 'staticfiles'
STATIC_URL = '/media/'

STATICFILES_DIRS = (
    os.path.abspath(os.path.join(BASE_DIR, '..', 'htdocs', 'media')),
)


TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'OPTIONS': {
        'debug': DEBUG,
        'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'mygpo.web.google.analytics',
                'mygpo.web.google.adsense',
                # make the debug variable available in templates
                # https://docs.djangoproject.com/en/dev/ref/templates/api/#django-core-context-processors-debug
                'django.template.context_processors.debug',

                # required so that the request obj can be accessed from
                # templates. this is used to direct users to previous
                # page after login
                'django.template.context_processors.request',
        ],
        'libraries': {
            'staticfiles' : 'django.templatetags.static',
        },
        'loaders': [
            ('django.template.loaders.cached.Loader', [
                'django.template.loaders.app_directories.Loader',
            ]),
        ],
    },
}]


MIDDLEWARE = [
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

ROOT_URLCONF = 'mygpo.urls'

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.admin',
    'django.contrib.humanize',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'djcelery',
    'mygpo.core',
    'mygpo.podcasts',
    'mygpo.chapters',
    'mygpo.search',
    'mygpo.users',
    'mygpo.api',
    'mygpo.web',
    'mygpo.publisher',
    'mygpo.subscriptions',
    'mygpo.history',
    'mygpo.favorites',
    'mygpo.usersettings',
    'mygpo.data',
    'mygpo.userfeeds',
    'mygpo.suggestions',
    'mygpo.directory',
    'mygpo.categories',
    'mygpo.episodestates',
    'mygpo.maintenance',
    'mygpo.share',
    'mygpo.administration',
    'mygpo.pubsub',
    'mygpo.podcastlists',
    'mygpo.votes',
    'django_nose',
]

try:
    if DEBUG:
        import debug_toolbar
        INSTALLED_APPS += ['debug_toolbar']
        MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

except ImportError:
    pass


try:
    import opbeat

    if not DEBUG:
        INSTALLED_APPS += ['opbeat.contrib.django']

except ImportError:
    pass


ACCOUNT_ACTIVATION_DAYS = int(os.getenv('ACCOUNT_ACTIVATION_DAYS', 7))

AUTHENTICATION_BACKENDS = (
    'mygpo.users.backend.CaseInsensitiveModelBackend',
    'mygpo.web.auth.EmailAuthenticationBackend',
)

SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

# TODO: use (default) JSON serializer for security
# this would currently fail as we're (de)serializing datetime objects
# https://docs.djangoproject.com/en/1.5/topics/http/sessions/#session-serialization
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'


MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

USER_CLASS = 'mygpo.users.models.User'

LOGIN_URL = '/login/'

CSRF_FAILURE_VIEW = 'mygpo.web.views.csrf_failure'


DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', '')

SECRET_KEY = os.getenv('SECRET_KEY', '')

if 'test' in sys.argv:
    SECRET_KEY = 'test'

GOOGLE_ANALYTICS_PROPERTY_ID = os.getenv('GOOGLE_ANALYTICS_PROPERTY_ID', '')

DIRECTORY_EXCLUDED_TAGS = os.getenv('DIRECTORY_EXCLUDED_TAGS', '').split()

FLICKR_API_KEY = os.getenv('FLICKR_API_KEY', '')

SOUNDCLOUD_CONSUMER_KEY = os.getenv('SOUNDCLOUD_CONSUMER_KEY', '')

MAINTENANCE = get_bool('MAINTENANCE', False)


ALLOWED_HOSTS = ['*']


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
    },
    'handlers': {
        'console': {
            'level': os.getenv('LOGGING_CONSOLE_LEVEL', 'DEBUG'),
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': os.getenv('LOGGING_DJANGO_HANDLERS',
                                  'console').split(),
            'propagate': True,
            'level': os.getenv('LOGGING_DJANGO_LEVEL', 'WARN'),
        },
        'mygpo': {
            'handlers': os.getenv('LOGGING_MYGPO_HANDLERS', 'console').split(),
            'level': os.getenv('LOGGING_MYGPO_LEVEL', 'INFO'),
        },
        'celery': {
            'handlers': os.getenv('LOGGING_CELERY_HANDLERS',
                                  'console').split(),
            'level': os.getenv('LOGGING_CELERY_LEVEL', 'DEBUG'),
        },
    },
}

_use_log_file = bool(os.getenv('LOGGING_FILENAME', False))

if _use_log_file:
    LOGGING['handlers']['file'] = {
        'level': 'INFO',
        'class': 'logging.handlers.RotatingFileHandler',
        'filename': os.getenv('LOGGING_FILENAME'),
        'maxBytes': 10000000,
        'backupCount': 10,
        'formatter': 'verbose',
    }


# minimum number of subscribers a podcast must have to be assigned a slug
PODCAST_SLUG_SUBSCRIBER_LIMIT = int(os.getenv(
                                    'PODCAST_SLUG_SUBSCRIBER_LIMIT', 10))

# minimum number of subscribers that a podcast needs to "push" one of its
# categories to the top
MIN_SUBSCRIBERS_CATEGORY = int(os.getenv('MIN_SUBSCRIBERS_CATEGORY', 10))

# maximum number of episode actions that the API processes immediatelly before
# returning the response. Larger requests will be handled in background.
# Handler can be set to None to disable
API_ACTIONS_MAX_NONBG = int(os.getenv('API_ACTIONS_MAX_NONBG', 100))
API_ACTIONS_BG_HANDLER = 'mygpo.api.tasks.episode_actions_celery_handler'


ADSENSE_CLIENT = os.getenv('ADSENSE_CLIENT', '')

ADSENSE_SLOT_BOTTOM = os.getenv('ADSENSE_SLOT_BOTTOM', '')

# we're running behind a proxy that sets the X-Forwarded-Proto header correctly
# see https://docs.djangoproject.com/en/dev/ref/settings/#secure-proxy-ssl-header
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# enabled access to staff-only areas with ?staff=<STAFF_TOKEN>
STAFF_TOKEN = os.getenv('STAFF_TOKEN', None)

# Flattr settings -- available after you register your app
FLATTR_KEY = os.getenv('FLATTR_KEY', '')
FLATTR_SECRET = os.getenv('FLATTR_SECRET', '')

# Flattr thing of the webservice. Will be flattr'd when a user sets
# the "Auto-Flattr gpodder.net" option
FLATTR_MYGPO_THING = os.getenv(
    'FLATTR_MYGPO_THING',
    'https://flattr.com/submit/auto?user_id=stefankoegl&url=http://gpodder.net'
)

# The User-Agent string used for outgoing HTTP requests
USER_AGENT = 'gpodder.net (+https://github.com/gpodder/mygpo)'

# Base URL of the website that is used if the actually used parameters is not
# available.  Request handlers, for example, can access the requested domain.
# Code that runs in background can not do this, and therefore requires a
# default value. This should be set to something like 'http://example.com'
DEFAULT_BASE_URL = os.getenv('DEFAULT_BASE_URL', '')


### Celery

BROKER_URL = os.getenv('BROKER_URL', 'redis://localhost')
CELERY_RESULT_BACKEND = 'djcelery.backends.database:DatabaseBackend'

SERVER_EMAIL = os.getenv('SERVER_EMAIL', 'no-reply@example.com')

CELERY_TASK_RESULT_EXPIRES = 60 * 60  # 1h expiry time in seconds

CELERY_ACCEPT_CONTENT = ['pickle', 'json']

CELERY_SEND_TASK_ERROR_EMAILS = get_bool('CELERY_SEND_TASK_ERROR_EMAILS',
                                         False)

BROKER_POOL_LIMIT = get_intOrNone('BROKER_POOL_LIMIT', 10)

### Google API

GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', '')

# URL where users of the site can get support
SUPPORT_URL = os.getenv('SUPPORT_URL', '')


FEEDSERVICE_URL = os.getenv('FEEDSERVICE_URL', 'http://feeds.gpodder.net/')

# Elasticsearch settings

ELASTICSEARCH_SERVER = os.getenv('ELASTICSEARCH_SERVER', '127.0.0.1:9200')
ELASTICSEARCH_INDEX = os.getenv('ELASTICSEARCH_INDEX', 'mygpo')
ELASTICSEARCH_TIMEOUT = float(os.getenv('ELASTICSEARCH_TIMEOUT', '2'))

# time for how long an activation is valid; after that, an unactivated user
# will be deleted
ACTIVATION_VALID_DAYS = int(os.getenv('ACTIVATION_VALID_DAYS', 10))


OPBEAT = {
    "ORGANIZATION_ID": os.getenv('OPBEAT_ORGANIZATION_ID', ''),
    "APP_ID": os.getenv('OPBEAT_APP_ID', ''),
    "SECRET_TOKEN": os.getenv('OPBEAT_SECRET_TOKEN', ''),
}

LOCALE_PATHS = [
    os.path.abspath(os.path.join(BASE_DIR, 'locale')),
]

INTERNAL_IPS = os.getenv('INTERNAL_IPS', '').split()

EMAIL_BACKEND = os.getenv('EMAIL_BACKEND',
                          'django.core.mail.backends.smtp.EmailBackend')

PODCAST_AD_ID = os.getenv('PODCAST_AD_ID')

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

NOSE_ARGS = [
    '--with-doctest',
    '--stop',
    '--where=mygpo',
]
