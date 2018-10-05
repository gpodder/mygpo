.. _configuration:

Configuration
=============

The following configuration parameters can be set through environment variables.


General
-------

* ``ADMINS`` - corresponds to `Django's ADMINS setting <https://docs.djangoproject.com/en/dev/ref/settings/#admins>`_. Specified as ``Name <email@host.com>``. Multiple entries can be separated by whitespace.
* ``DEBUG`` - Debug flug, see `Django's DEBUG setting <https://docs.djangoproject.com/en/1.11/ref/settings/#std:setting-DEBUG>`_
* ``DEFAULT_BASE_URL`` - base URL for creating URLs, eg ``https://gpodder.net``
* ``GOOGLE_ANALYTICS_PROPERTY_ID`` - Google Analytics Property ID
* ``MAINTENANCE`` - Maintenance flag
* ``SECRET_KEY`` - see `Django's SECRET_KEY setting <https://docs.djangoproject.com/en/1.11/ref/settings/#secret-key>`_
* ``STAFF_TOKEN`` - token which can be appended to URLs to access staff-only pages
* ``SUPPORT_URL`` - URL where users can get support


Advertising
-----------

* ``ADSENSE_CLIENT`` - Google AdSense Client ID
* ``ADSENSE_SLOT_BOTTOM``- Ad for the ad slot on the bottom of the page
* ``PODCAST_AD_ID`` - Database Id of the podcast which is currently advertising


Celery Task Queue
-----------------

* ``BROKER_POOL_LIMIT`` - corresponds to `Celery's broker_pool_limit setting <http://docs.celeryproject.org/en/latest/userguide/configuration.html#broker-pool-limit>`_. Specifies the maximum number of connections that can be open in the connection pool.
* ``BROKER_URL`` - corresponds to `Celery's broker_url setting <http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-broker_url>`_. Specifies the URL / connection string to the broker.


Caching
-------

The following settings correspond to `Django's CACHE setting
<https://docs.djangoproject.com/en/1.11/ref/settings/#std:setting-CACHES>`_.

* ``CACHE_BACKEND`` - Django cache backend
* ``CACHE_LOCATION`` - Location of the cache


Database
--------

* ``DATABASE_URL`` - Database connection string, see `syntax and options <https://github.com/kennethreitz/dj-database-url>`_.


Emails
------

* ``DEFAULT_FROM_EMAIL`` - From address for outgoing emails, see `Django's DEFAULT_FROM_EMAIL setting <https://docs.djangoproject.com/en/1.11/ref/settings/#default-from-email>`_.


Search
------

* ``ELASTICSEARCH_SERVER`` - ``host:port`` of the Elasticsearch server
* ``ELASTICSEARCH_TIMEOUT`` - timeout in seconds for queries to the Elasticsearch server


Directory
---------

* ``DIRECTORY_EXCLUDED_TAGS`` - space-separated list of tags that should be excluded from the podcast directory
* ``SEARCH_CUTOFF`` - minimum search rank (between 0 and 1, default 0.3) below which results are excluded. See `Django's documentation on Weighting queries <https://docs.djangoproject.com/en/1.11/ref/contrib/postgres/search/#weighting-queries>`_


Feeds
-----

* ``FLICKR_API_KEY`` - Flickr API key
* ``SOUNDCLOUD_CONSUMER_KEY`` - Soundcloud Consumer key


Logging
-------

* ``SERVER_EMAIL`` - email address from which error mails are sent, see `Django's SERVER_EMAIL setting <https://docs.djangoproject.com/en/1.11/ref/settings/#server-email>`_
* ``LOGGING_CELERY_HANDLERS`` - space separated list of logging handlers for Celery log events
* ``LOGGING_DJANGO_HANDLERS`` - space separated list of logging handlers for Django log events
* ``LOGGING_MYGPO_HANDLERS`` - space separated list of logging handlers for mygpo log events
* ``LOGGING_FILENAME`` - filename for filesystem logs
* ``OPBEAT_APP_ID`` - Opbeat App ID
* ``OPBEAT_ORGANIZATION_ID`` - Opbeat Organization ID
* ``OPBEAT_SECRET_TOKEN`` - Opbeat Secret Token


Social Login
------------

* ``GOOGLE_CLIENT_ID`` - Google Client ID
* ``GOOGLE_CLIENT_SECRET`` - Google Client Secret


API
---
* ``MAX_EPISODE_ACTIONS`` - maximum number of episode actions that the API will return in one `GET` request.
