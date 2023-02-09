import re
import sys
import os.path
import dj_database_url


try:
    from psycopg2cffi import compat

    compat.register()
except ImportError:
    pass


import django
import six
from configurations import Configuration

django.utils.six = six

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_bool(name, default):
    return os.getenv(name, str(default)).lower() == "true"


def get_intOrNone(name, default):
    """Parses the env variable, accepts ints and literal None"""
    value = os.getenv(name, str(default))
    if value.lower() == "none":
        return None
    return int(value)


class BaseConfig(Configuration):

    DEBUG = get_bool("DEBUG", False)

    ADMINS = re.findall(r"\s*([^<]+) <([^>]+)>\s*", os.getenv("ADMINS", ""))

    MANAGERS = ADMINS

    _DATABASES = {
        "default": dj_database_url.config(default="postgres://mygpo:mygpo@localhost/mygpo")
    }
    _USE_GEVENT = get_bool("USE_GEVENT", False)

    @property
    def DATABASES(self):
        if self._USE_GEVENT:
        # see https://github.com/jneight/django-db-geventpool
            default = self._DATABASES["default"]
            default["ENGINE"] = ("django_db_geventpool.backends.postgresql_psycopg2",)
            default["CONN_MAX_AGE"] = 0
            options = default.get("OPTIONS", {})
            options["MAX_CONNS"] = 20
        return self._DATABASES

    _cache_used = bool(os.getenv("CACHE_BACKEND", False))

    @property
    def CACHES(self):
        # Set the default django backend as a fallback
        CACHES = Configuration.CACHES
        if self._cache_used:
            CACHES["default"] = {
                "BACKEND": os.getenv(
                    "CACHE_BACKEND", "django.core.cache.backends.memcached.MemcachedCache"
                ),
                "LOCATION": os.getenv("CACHE_LOCATION"),
            }
        return CACHES

    # Local time zone for this installation. Choices can be found here:
    # http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
    # although not all choices may be available on all operating systems.
    # If running in a Windows environment this must be set to the same as your
    # system time zone.
    TIME_ZONE = "UTC"

    # Language code for this installation. All choices can be found here:
    # http://www.i18nguy.com/unicode/language-identifiers.html
    LANGUAGE_CODE = "en-us"

    SITE_ID = 1

    # If you set this to False, Django will make some optimizations so as not
    # to load the internationalization machinery.
    USE_I18N = True


    # Static Files

    STATIC_ROOT = "staticfiles"
    STATIC_URL = "/static/"

    STATICFILES_DIRS = (os.path.abspath(os.path.join(BASE_DIR, "..", "static")),)


    # Media Files

    MEDIA_ROOT = os.getenv(
        "MEDIA_ROOT", os.path.abspath(os.path.join(BASE_DIR, "..", "media"))
    )

    MEDIA_URL = "/media/"

    TEMPLATES = [
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [],
            "OPTIONS": {
                "debug": DEBUG,
                "context_processors": [
                    "django.contrib.auth.context_processors.auth",
                    "django.template.context_processors.debug",
                    "django.template.context_processors.i18n",
                    "django.template.context_processors.media",
                    "django.template.context_processors.static",
                    "django.template.context_processors.tz",
                    "django.contrib.messages.context_processors.messages",
                    "mygpo.web.google.analytics",
                    "mygpo.web.google.adsense",
                    # make the debug variable available in templates
                    # https://docs.djangoproject.com/en/dev/ref/templates/api/#django-core-context-processors-debug
                    "django.template.context_processors.debug",
                    # required so that the request obj can be accessed from
                    # templates. this is used to direct users to previous
                    # page after login
                    "django.template.context_processors.request",
                ],
                "libraries": {"staticfiles": "django.templatetags.static"},
                "loaders": [
                    (
                        "django.template.loaders.cached.Loader",
                        ["django.template.loaders.app_directories.Loader"],
                    )
                ],
            },
        }
    ]


    MIDDLEWARE = [
        "django.middleware.common.CommonMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.middleware.locale.LocaleMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
    ]

    ROOT_URLCONF = "mygpo.urls"

    INSTALLED_APPS = [
        "django.contrib.contenttypes",
        "django.contrib.messages",
        "django.contrib.admin",
        "django.contrib.humanize",
        "django.contrib.auth",
        "django.contrib.sessions",
        "django.contrib.staticfiles",
        "django.contrib.sites",
        "django.contrib.postgres",
        "django_celery_results",
        "django_celery_beat",
        "mygpo.core",
        "mygpo.podcasts",
        "mygpo.chapters",
        "mygpo.search",
        "mygpo.users",
        "mygpo.api",
        "mygpo.web",
        "mygpo.publisher",
        "mygpo.subscriptions",
        "mygpo.history",
        "mygpo.favorites",
        "mygpo.usersettings",
        "mygpo.data",
        "mygpo.userfeeds",
        "mygpo.suggestions",
        "mygpo.directory",
        "mygpo.categories",
        "mygpo.episodestates",
        "mygpo.maintenance",
        "mygpo.share",
        "mygpo.administration",
        "mygpo.pubsub",
        "mygpo.podcastlists",
        "mygpo.votes",
    ]

    ACCOUNT_ACTIVATION_DAYS = int(os.getenv("ACCOUNT_ACTIVATION_DAYS", 7))

    AUTHENTICATION_BACKENDS = (
        "mygpo.users.backend.CaseInsensitiveModelBackend",
        "mygpo.web.auth.EmailAuthenticationBackend",
    )

    SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

    # TODO: use (default) JSON serializer for security
    # this would currently fail as we're (de)serializing datetime objects
    # https://docs.djangoproject.com/en/1.5/topics/http/sessions/#session-serialization
    SESSION_SERIALIZER = "django.contrib.sessions.serializers.PickleSerializer"


    MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"

    USER_CLASS = "mygpo.users.models.User"

    LOGIN_URL = "/login/"

    CSRF_FAILURE_VIEW = "mygpo.web.views.csrf_failure"


    DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "")

    SERVER_EMAIL = os.getenv("SERVER_EMAIL", DEFAULT_FROM_EMAIL)

    SECRET_KEY = os.getenv("SECRET_KEY", "")

    GOOGLE_ANALYTICS_PROPERTY_ID = os.getenv("GOOGLE_ANALYTICS_PROPERTY_ID", "")

    DIRECTORY_EXCLUDED_TAGS = os.getenv("DIRECTORY_EXCLUDED_TAGS", "").split()

    FLICKR_API_KEY = os.getenv("FLICKR_API_KEY", "")

    SOUNDCLOUD_CONSUMER_KEY = os.getenv("SOUNDCLOUD_CONSUMER_KEY", "")

    MAINTENANCE = get_bool("MAINTENANCE", False)

    ALLOWED_HOSTS = ["*"]

    _LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "verbose": {"format": "%(asctime)s %(name)s %(levelname)s %(message)s"}
        },
        "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
        "handlers": {
            "console": {
                "level": os.getenv("LOGGING_CONSOLE_LEVEL", "DEBUG"),
                "class": "logging.StreamHandler",
                "formatter": "verbose",
            },
            "mail_admins": {
                "level": "ERROR",
                "filters": ["require_debug_false"],
                "class": "django.utils.log.AdminEmailHandler",
            },
        },
        "loggers": {
            "django": {
                "handlers": os.getenv("LOGGING_DJANGO_HANDLERS", "console").split(),
                "propagate": True,
                "level": os.getenv("LOGGING_DJANGO_LEVEL", "WARN"),
            },
            "mygpo": {
                "handlers": os.getenv("LOGGING_MYGPO_HANDLERS", "console").split(),
                "level": os.getenv("LOGGING_MYGPO_LEVEL", "INFO"),
            },
            "celery": {
                "handlers": os.getenv("LOGGING_CELERY_HANDLERS", "console").split(),
                "level": os.getenv("LOGGING_CELERY_LEVEL", "DEBUG"),
            },
        },
    }

    _use_log_file = bool(os.getenv("LOGGING_FILENAME", False))

    @property
    def LOGGING(self):
        if self._use_log_file:
            self._LOGGING["handlers"]["file"] = {
                "level": "INFO",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": os.getenv("LOGGING_FILENAME"),
                "maxBytes": 10_000_000,
                "backupCount": 10,
                "formatter": "verbose",
            }
        return self._LOGGING

    DATA_UPLOAD_MAX_MEMORY_SIZE = get_intOrNone("DATA_UPLOAD_MAX_MEMORY_SIZE", None)

    # minimum number of subscribers a podcast must have to be assigned a slug
    PODCAST_SLUG_SUBSCRIBER_LIMIT = int(os.getenv("PODCAST_SLUG_SUBSCRIBER_LIMIT", 10))

    # minimum number of subscribers that a podcast needs to "push" one of its
    # categories to the top
    MIN_SUBSCRIBERS_CATEGORY = int(os.getenv("MIN_SUBSCRIBERS_CATEGORY", 10))

    # maximum number of episode actions that the API processes immediatelly before
    # returning the response. Larger requests will be handled in background.
    # Handler can be set to None to disable
    API_ACTIONS_MAX_NONBG = get_intOrNone("API_ACTIONS_MAX_NONBG", 100)
    API_ACTIONS_BG_HANDLER = "mygpo.api.tasks.episode_actions_celery_handler"

    ADSENSE_CLIENT = os.getenv("ADSENSE_CLIENT", "")

    ADSENSE_SLOT_BOTTOM = os.getenv("ADSENSE_SLOT_BOTTOM", "")

    # we're running behind a proxy that sets the X-Forwarded-Proto header correctly
    # see https://docs.djangoproject.com/en/dev/ref/settings/#secure-proxy-ssl-header
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

    # enabled access to staff-only areas with ?staff=<STAFF_TOKEN>
    STAFF_TOKEN = os.getenv("STAFF_TOKEN", None)

    # The User-Agent string used for outgoing HTTP requests
    USER_AGENT = "gpodder.net (+https://github.com/gpodder/mygpo)"

    # Base URL of the website that is used if the actually used parameters is not
    # available.  Request handlers, for example, can access the requested domain.
    # Code that runs in background can not do this, and therefore requires a
    # default value. This should be set to something like 'http://example.com'
    DEFAULT_BASE_URL = os.getenv("DEFAULT_BASE_URL", "")

    ### Celery

    CELERY_BROKER_URL = os.getenv("BROKER_URL", "redis://localhost")
    CELERY_RESULT_BACKEND = os.getenv("BROKER_BACKEND", "django-db")

    CELERY_RESULT_EXPIRES = 60 * 60  # 1h expiry time in seconds

    CELERY_ACCEPT_CONTENT = ["json"]

    ### Google API

    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

    # URL where users of the site can get support
    SUPPORT_URL = os.getenv("SUPPORT_URL", "")

    FEEDSERVICE_URL = os.getenv("FEEDSERVICE_URL", "http://feeds.gpodder.net/")

    # time for how long an activation is valid; after that, an unactivated user
    # will be deleted
    ACTIVATION_VALID_DAYS = int(os.getenv("ACTIVATION_VALID_DAYS", 10))

    OPBEAT = {
        "ORGANIZATION_ID": os.getenv("OPBEAT_ORGANIZATION_ID", ""),
        "APP_ID": os.getenv("OPBEAT_APP_ID", ""),
        "SECRET_TOKEN": os.getenv("OPBEAT_SECRET_TOKEN", ""),
    }

    LOCALE_PATHS = [os.path.abspath(os.path.join(BASE_DIR, "locale"))]

    INTERNAL_IPS = os.getenv("INTERNAL_IPS", "").split()

    EMAIL_BACKEND = os.getenv(
        "EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend"
    )

    PODCAST_AD_ID = os.getenv("PODCAST_AD_ID")

    MAX_EPISODE_ACTIONS = int(os.getenv("MAX_EPISODE_ACTIONS", 1000))

    SEARCH_CUTOFF = float(os.getenv("SEARCH_CUTOFF", 0.3))

    # Maximum non-whitespace length of search query
    # If length of query is shorter than QUERY_LENGTH_CUTOFF, no results
    # will be returned to avoid a server timeout due to too many possible
    # responses
    QUERY_LENGTH_CUTOFF = int(os.getenv("QUERY_LENGTH_CUTOFF", 3))


class Local(BaseConfig):

    @classmethod
    def setup(cls):
        super(BaseConfig, cls).setup()
        if cls.DEBUG:
            try:
                import debug_toolbar
                cls.INSTALLED_APPS += ["debug_toolbar"]
                cls.MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
            except ImportError:
                pass
            try:
                import django_extensions
                cls.INSTALLED_APPS += ["django_extensions"]
            except ImportError:
                pass


class Test(BaseConfig):
    SECRET_KEY = "test"


class StorageMixin():
    DEFAULT_FILE_STORAGE = 'mygpo.storages.MediaStorage'
    STATICFILES_STORAGE = 'mygpo.storages.StaticStorage'
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_S3_ENDPOINT_URL = os.getenv('AWS_S3_ENDPOINT_URL', 'https://localhost:9000')
    AWS_S3_VERIFY = True
    AWS_S3_REGION_NAME = 'ams3'
    AWS_DEFAULT_ACL = 'public-read'
    AWS_QUERYSTRING_AUTH=False
    MEDIA_URL = os.getenv('AWS_S3_ENDPOINT_URL', 'https://localhost:9000/') + 'uploads/'
    STATIC_URL = os.getenv('AWS_S3_ENDPOINT_URL', 'https://localhost:9000/') + 'statics/'


class Prod(StorageMixin, BaseConfig):
    ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
    SITE_ID=1
    DEBUG = os.getenv('DEBUG', False)
    # SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    EMAIL_HOST = os.getenv('EMAIL_HOST', '')
    EMAIL_PORT = os.getenv('EMAIL_HOST_PORT', 587)
    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
    EMAIL_USE_TLS = True

    @property
    def INSTALLED_APPS(self):
        installed_apps = super().INSTALLED_APPS[:]
        return installed_apps + [
            'health_check',
            'health_check.db',
            'health_check.cache',
            'health_check.storage',
            'health_check.contrib.migrations',
        ]

    @classmethod
    def post_setup(cls):
        """Sentry initialization"""
        super(Prod, cls).post_setup()
        ### Sentry
        try:
            import sentry_sdk
            from sentry_sdk.integrations.django import DjangoIntegration
            from sentry_sdk.integrations.celery import CeleryIntegration
            from sentry_sdk.integrations.redis import RedisIntegration

            # Sentry Data Source Name (DSN)
            sentry_dsn = os.getenv("SENTRY_DSN", "")
            if not sentry_dsn:
                raise ValueError("Could not set up sentry because " "SENTRY_DSN is not set")

            sentry_sdk.init(
                dsn=sentry_dsn,
                integrations=[DjangoIntegration(), CeleryIntegration(), RedisIntegration()],
                send_default_pii=True,
            )

        except (ImportError, ValueError):
            pass
