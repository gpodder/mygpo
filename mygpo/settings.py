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

DATABASES = {
    'default': {
        'NAME':     'mygpo',
        'ENGINE':   'django.db.backends.sqlite3',
        'USER':     '',
        'PASSWORD': '',
        'HOST':     '',
    }
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

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/admin/'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.locale.LocaleMiddleware',
)

ROOT_URLCONF = 'mygpo.urls'

TEMPLATE_DIRS = ()

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.humanize',
    'registration',
    'mygpo.api',
    'mygpo.web',
    'mygpo.publisher',
    'mygpo.data',
    'mygpo.userfeeds',
)

ACCOUNT_ACTIVATION_DAYS = 7

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'mygpo.auth_backends.EmailAuthenticationBackend',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.contrib.messages.context_processors.messages",
    "mygpo.web.googleanalytics.processor",
)


AUTH_PROFILE_MODULE = "api.UserProfile"

LOGIN_URL = '/login/'

CSRF_FAILURE_VIEW='mygpo.security.csrf_failure'


# The following entries should be set in settings_prod.py
DEFAULT_FROM_EMAIL = ''
SECRET_KEY = ''
GOOGLE_ANALYTICS_PROPERTY_ID=''
DIRECTORY_EXCLUDED_TAGS = ()
FLICKR_API_KEY = ''


try:
    from settings_prod import *
except ImportError, e:
     import sys
     print >> sys.stderr, 'create settings_prod.py with your customized settings'

