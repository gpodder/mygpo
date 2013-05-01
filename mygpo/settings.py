# Django settings for mygpo project.
#
# This file is part of my.gpodder.org.
#
# my.gpodder.org is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# my.gpodder.org is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public
# License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with my.gpodder.org. If not, see <http://www.gnu.org/licenses/>.
#

import os.path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# http://code.djangoproject.com/wiki/BackwardsIncompatibleChanges#ChangedthewayURLpathsaredetermined
FORCE_SCRIPT_NAME=""

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = ()

MANAGERS = ADMINS

# dummy entry.
# not needed for production, but tests fail otherwise in Django 1.4
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'tmp',
    }
}

COUCHDB_DATABASES = {
    'mygpo.directory':
        {'URL': 'http://127.0.0.1:5984/mygpo'},

    'mygpo.core':
        {'URL': 'http://127.0.0.1:5984/mygpo'},

    'mygpo.api':
        {'URL': 'http://127.0.0.1:5984/mygpo'},

    'mygpo.users':
        {'URL': 'http://127.0.0.1:5984/mygpo'},

    'mygpo.share':
        {'URL': 'http://127.0.0.1:5984/mygpo'},

    'mygpo.maintenance':
        {'URL': 'http://127.0.0.1:5984/mygpo'},

    'django_couchdb_utils_auth':
        {'URL': 'http://127.0.0.1:5984/mygpo'},

    'django_couchdb_utils_sessions':
        {'URL': 'http://127.0.0.1:5984/mygpo_sessions'},

    'django_couchdb_utils_registration':
        {'URL': 'http://127.0.0.1:5984/mygpo'},
}

# Maps design documents to databases. The keys correspond to the directories in
# mygpo/couch/, the values are the app labels which are mapped to the actual
# databases in COUCHDB_DATABASES. This indirect mapping is used because
# COUCHDB_DATABASES is likely to be overwritten in settings_prod.py while
# COUCHDB_DDOC_MAPPING is most probably not overwritten.
COUCHDB_DDOC_MAPPING = {
    'general':    'core',
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

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.abspath('%s/../htdocs/media/' % os.path.dirname(__file__))

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'mygpo.urls'

TEMPLATE_DIRS = ()

INSTALLED_APPS = (
    'django.contrib.contenttypes',  # unused, but tests fail otherwise (?)
    'django.contrib.messages',
    'django.contrib.humanize',
    'couchdbkit.ext.django',
    'django_couchdb_utils.auth',
    'django_couchdb_utils.sessions',
    'django_couchdb_utils.registration',
    'mygpo.core',
    'mygpo.users',
    'mygpo.api',
    'mygpo.web',
    'mygpo.publisher',
    'mygpo.data',
    'mygpo.userfeeds',
    'mygpo.directory',
    'mygpo.maintenance',
    'mygpo.share',
    'mygpo.admin',
    'mygpo.db.couchdb',
)

TEST_EXCLUDE = (
    'django',
    'couchdbkit',
)

TEST_RUNNER='mygpo.test.MygpoTestSuiteRunner'

ACCOUNT_ACTIVATION_DAYS = 7

AUTHENTICATION_BACKENDS = (
    'django_couchdb_utils.auth.backends.CouchDBAuthBackend',
    'mygpo.web.auth.EmailAuthenticationBackend',
)

SESSION_ENGINE = "django_couchdb_utils.sessions.cached_couchdb"

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.contrib.messages.context_processors.messages",
    "mygpo.web.google.analytics",
    "mygpo.web.google.adsense",
)

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

USER_CLASS = 'mygpo.users.models.User'

AUTH_PROFILE_MODULE = "api.UserProfile"


LOGIN_URL = '/login/'

CSRF_FAILURE_VIEW='mygpo.web.views.security.csrf_failure'


# The following entries should be set in settings_prod.py
DEFAULT_FROM_EMAIL = ''
SECRET_KEY = ''
GOOGLE_ANALYTICS_PROPERTY_ID=''
DIRECTORY_EXCLUDED_TAGS = ()
FLICKR_API_KEY = ''

MAINTENANCE = os.path.exists(os.path.join(BASE_DIR, 'MAINTENANCE'))

EMAIL_BACKEND = 'django_couchdb_utils.email.backends.CouchDBEmailBackend'

# minimum number of subscribers a podcast must have to be assigned a slug
PODCAST_SLUG_SUBSCRIBER_LIMIT = 10

# minimum number of subscribers that a podcast needs to "push" one of its
# categories to the top
MIN_SUBSCRIBERS_CATEGORY=10

# maximum number of episode actions that the API processes immediatelly before
# returning the response. Larger requests will be handled in background.
# Handler can be set to None to disable
API_ACTIONS_MAX_NONBG=100
API_ACTIONS_BG_HANDLER='mygpo.api.tasks.episode_actions_celery_handler'


ADSENSE_CLIENT = ''
ADSENSE_SLOT_BOTTOM = ''

# enabled access to staff-only areas with ?staff=<STAFF_TOKEN>
STAFF_TOKEN = None

# Flattr settings -- available after you register your app
FLATTR_KEY = ''
FLATTR_SECRET = ''

# Flattr thing of the webservice. Will be flattr'd when a user sets the "Auto-Flattr gpodder.net" option
FLATTR_MYGPO_THING='https://flattr.com/submit/auto?user_id=stefankoegl&url=http://gpodder.net'

# The User-Agent string used for outgoing HTTP requests
USER_AGENT = 'gpodder.net (+https://github.com/gpodder/mygpo)'



### Celery

BROKER_URL='redis://localhost'
BACKEND_URL='redis://localhost'


# a dictionary containing celery settings from
# http://docs.celeryproject.org/en/latest/configuration.html
CELERY_CONF = dict(
    CELERY_SEND_TASK_ERROR_EMAILS = True,
    ADMINS=ADMINS,
    SERVER_EMAIL = "no-reply@example.com",
)


### Google API

GOOGLE_CLIENT_ID=''
GOOGLE_CLIENT_SECRET=''



try:
    from settings_prod import *
except ImportError, e:
    import sys
    print >> sys.stderr, 'create settings_prod.py with your customized settings'
