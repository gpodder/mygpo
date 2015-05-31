Settings API
============

Clients can store settings and retrieve settings as key-value-pairs, which are
attached to either account, device, podcast or episode.

Keys are the names of the settings and are supposed to be strings. Values can
be any valid JSON objects.


Known Settings
--------------

Although settings are primarily used to exchange settings between clients, some
of them also trigger some behavior on the website.

Account
^^^^^^^

* ``public_profile``: when set to False, sets all podcasts to private
  (as on http://gpodder.net/account/privacy, currently deactivated via API)
* ``store_user_agent``: allow gpodder.net to store the User-Agent for each
  device (default: true)
* ``public_subscriptions``: default "public" value for subscriptions (default:
  true)
* ``flattr_token``: auth-token for a Flattr login; empty when not logged in
  (default: empty)
* ``auto_flattr``: auto-flattr episodes, only relevant when logged into Flattr
  account (default: false)
* ``flattr_mygpo``: automatically flattr gpodder.net, only relevant when logged
  into Flattr account (default: false)
* ``flattr_username``: username under which own items (eg podcast lists) are
  published (default: empty)

Episode
^^^^^^^

* ``is_favorite``: flags the episode as favorite (can be done on any
  episode-page)

Podcast
^^^^^^^

* ``public_subscription``: when set to False, sets the subscription to this
  podcast to private (as on http://gpodder.net/account/privacy or any
  podcast-page, currently deactivated via API)


Save Settings
-------------

..  http:post:: /api/2/settings/(username)/(scope).json
    :synopsis: Update or save some settings

    * Requires Authentication
    * Since 2.4

    **Example request**:

    .. sourcecode:: http

        {
            "set": {"setting1": "value1", "setting2": "value2"},
            "remove": ["setting3", "setting4"]
        }

    :param scope: one of account, device, podcast, episode
    :query string podcast: Feed URL of a podcast (required for scope podcast
                           and episode)
    :query device: Device id (see :ref:`devices`, required for scope device)
    :query episode: media URL of the episode (required for scope episode)

    set is a dictionary of settings to add or update; remove is a list of keys
    that shall be removed from the scope.

    **Example response**:

    The response contains all settings that the scope has after the update has
    been carried out.

    .. sourcecode: http

        HTTP/1.1 200 OK

        {
            "setting1": "value1",
            "setting2": "value"
        }


Get Settings
------------

..  http:get:: /api/2/settings/(username)/(scope).json
    :synopsis: retrieve current settings

    * Requires Authentication
    * Since 2.4

    :param scope: one of account, device, podcast, episode
    :query string podcast: Feed URL of a podcast (required for scope podcast
                           and episode)
    :query device: Device id (see :ref:`devices`, required for scope device)
    :query episode: media URL of the episode (required for scope episode)


    **Example response**:

    The response contains all settings that the scope currently has

    .. sourcecode:: http

        {
            "setting1": "value1",
            "setting2": "value2"
        }

