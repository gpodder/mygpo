Settings API
============

Clients can use the gpodder.net API to store and exchange settings. Clients can
chose to simply store their settings on gpodder.net for online backup, or
exchange settings with other clients. Some settings also trigger behaviour on
the gpodder.net website.

Settings can be stored in several scopes. Each user has one *account* scope,
and one *device* scope per device. Additionally settings can be stored
per *podcast* and *episode*.


Resources
---------

The Settings API defines the following resources ::

    /user/<username>/settings/account
    /user/<username>/settings/device
    /user/<username>/settings/podcast
    /user/<username>/settings/episode


Well-Known Settings
-------------------

Although settings are primarily used to exchange settings between clients, some
of them also trigger some behavior on the website.


Account scope
^^^^^^^^^^^^^

The following settings are well-known in the account scope.

**public_profile**
    when set to False, sets all podcasts to private (as on
    http://gpodder.net/account/privacy, currently deactivated via API)

**store_user_agent**
    allow gpodder.net to store the User-Agent for each
    device (default: true)

**public_subscriptions**
    default "public" value for subscriptions (default: true)

**flattr_token**
    auth-token for a Flattr login; empty when not logged in (default: empty)

**auto_flattr**
    auto-flattr episodes, only relevant when logged into Flattr account
    (default: false)

**flattr_mygpo**
    automatically flattr gpodder.net, only relevant when logged into Flattr
    account (default: false)

**flattr_username**
    username under which own items (eg podcast lists) are published
    (default: empty)


Episode scope
^^^^^^^^^^^^^

The following settings are well-known in the episode scope.

**is_favorite**
    flags the episode as favorite (can be done on any episode-page)


Podcast scope
^^^^^^^^^^^^^

The following settings are well-known in the podcast scope.

**public_subscription**
    when set to False, sets the subscription to this podcast to private
    (as on http://gpodder.net/account/privacy or any podcast-page, currently
    deactivated via API)


Saving Settings
---------------

Save Settings ::

    POST /user/<username>/settings/<scope>?<scope-specification>


* Requires authentication


Parameters
^^^^^^^^^^

**scope**
  can be either ``account``, ``device``, ``podcast`` or ``episode``

**podcast**
  should contain the URL-encoded feed URL when ``scope`` is ``podcast`` or ``episode``

**episode**
  should contain the URL-encoded media URL when ``scope`` is ``episode``

**device**
  should contain the device Id when ``scope`` is ``device``


Request Body
^^^^^^^^^^^^

TODO: JSON-Patch ?

Post-Data ::

    {
     "set": {"setting1": "value1", "setting2": "value2"},
     "remove": ["setting3", "setting4"]
    }

set is a dictionary of settings to add or update; remove is a list of keys that
shall be removed from the scope.

Response
^^^^^^^^

The response contains all settings that the scope has after the update has been
carried out. ::

    {
     "setting1": "value1",
     "setting2": "value"
    }



Get Settings
------------

Get Settings ::

    GET /user/<username>/settings/<scope>?<scope-specification>

Scope and specification as above.
Requires Authentication


Response
^^^^^^^^

The response contains all settings that the scope currently has ::

    {"setting1": "value1", "setting2": "value2"}
