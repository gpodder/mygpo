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
    PATCH /user/<username>/settings/<scope>?<scope-specification>


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

The request body consists basically of a `JSON Patch (RFC 6902)
<http://tools.ietf.org/html/rfc6902>`_. However there are two possible
representations for a patch.

When the PATCH method is used, the body corresponds to the JSON Patch. ::

   [
     { "op": "test", "path": "/a/b/c", "value": "foo" },
     { "op": "remove", "path": "/a/b/c" },
     { "op": "add", "path": "/a/b/c", "value": [ "foo", "bar" ] },
     { "op": "replace", "path": "/a/b/c", "value": 42 },
     { "op": "move", "from": "/a/b/c", "path": "/a/b/d" },
     { "op": "copy", "from": "/a/b/d", "path": "/a/b/e" }
   ]


When a POST request is used, a JSON object is included in the body, where the
actual patch is provided in the *patch* attribute. ::

    {
        patch: [
            { "op": "test", "path": "/a/b/c", "value": "foo" },
            { "op": "remove", "path": "/a/b/c" },
            { "op": "add", "path": "/a/b/c", "value": [ "foo", "bar" ] },
            { "op": "replace", "path": "/a/b/c", "value": 42 },
            { "op": "move", "from": "/a/b/c", "path": "/a/b/d" },
            { "op": "copy", "from": "/a/b/d", "path": "/a/b/e" }
        ]
    }

Please refer to `RFC 6902 <http://tools.ietf.org/html/rfc6902>`_ for the
allowed operations and exact semantics of JSON Patch. Previously unused
settings default to the empty JSON object (``{}``).


Response
^^^^^^^^

Status Codes:

* 200 OK
* 409 Conflict if a test operation failed

A positive response contains all settings that the scope has after the update
has been carried out. ::

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
