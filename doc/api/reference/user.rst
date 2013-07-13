User API
========

The User API can be used to retrieve public information about a user, and to
discover user-related resources.

When initiating a session, a client SHOULD query the user information, to
discover URIs for further queries.


Resources
---------

The User API defines the following resources ::

  /user/{username}


Get User Info
-------------

Request ::

    GET /user/{username}
    Content-Tpe: application/json


Response::

    200 Found
    Content-Tpe: application/json

    {
        "username": "stefan",
        "avatar": "http://....",
        "twitter": "@skoegl",
        "description": "hi...",
        "flattr_username": "stefankoegl",

        "resources": {
            "subscriptions": "http://api.gpodder.net/3/user/{username}/subscriptions",
            ...
        }
    }

