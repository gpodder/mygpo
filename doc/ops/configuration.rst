Configuration
=============

Configuration can be done through the following environment variables.

``DEBUG``
---------
Debug mode shows error pages, enables debug output, etc.


``DATABASE_URL``
----------------
DB connection string in the form of ``postgres://USER:PASSWORD@HOST:PORT/NAME``


``ACCOUNT_ACTIVATION_DAYS``
---------------------------
Number of days that newly registered users have time to activate their account.


``DEFAULT_FROM_EMAIL``
----------------------
Default sender address for outgoing emails. See `Django documentation
<https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-DEFAULT_FROM_EMAIL>`__.


``SECRET_KEY``
--------------
See `Django documentation
<https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-SECRET_KEY>`__.


``GOOGLE_ANALYTICS_PROPERTY_ID``
--------------------------------
Setting a Google Analytics Property ID activates GA integration.


``DIRECTORY_EXCLUDED_TAGS``
---------------------------
A comma-separated list of tags that are excluded from the directory.


``FLICKR_API_KEY``
------------------
Setting a Flickr API key activates Flickr integration.


``MAINTENANCE``
---------------
Switches the site into a maintenance mode.


* ``PODCAST_SLUG_SUBSCRIBER_LIMIT``

* ``MIN_SUBSCRIBERS_CATEGORY``:  minimum number of subscribers that a podcast
  needs to "push" one of its categories to the top

* ``API_ACTIONS_MAX_NONBG``: maximum number of episode actions that the API
  processes immediatelly before returning the response. Larger requests will
  be handled in background.

* ``ADSENSE_CLIENT``

* ``ADSENSE_SLOT_BOTTOM``

* ``STAFF_TOKEN``: enabled access to staff-only areas with ?staff=<STAFF_TOKEN>

* ``FLATTR_KEY``

* ``FLATTR_SECRET``

* ``FLATTR_MYGPO_THING``: Flattr thing of the webservice. Will be flattr'd
  when a user sets the "Auto-Flattr gpodder.net" option

* ``USER_AGENT``: The User-Agent string used for outgoing HTTP requests

* ``DEFAULT_BASE_URL``: Base URL of the website that is used if the actually
  used parameters is not available. Request handlers, for example, can access
  the requested domain. Code that runs in background can not do this, and
  therefore requires a default value. This should be set to something like
  ``http://example.com``

* ``BROKER_URL`` Celery Broker URL

* ``CELERY_RESULT_BACKEND``

* ``CELERY_SEND_TASK_ERROR_EMAILS``

* ``SERVER_EMAIL``

* ``GOOGLE_CLIENT_ID``

* ``GOOGLE_CLIENT_SECRET``

* ``SUPPORT_URL``: URL where users of the site can get support

* ``ELASTICSEARCH_SERVER``

* ``ELASTICSEARCH_INDEX``

* ``ELASTICSEARCH_TIMEOUT``

* ``ACTIVATION_VALID_DAYS`` time for how long an activation is valid; after
  that, an unactivated user will be deleted

* ``INTERNAL_IPS``
