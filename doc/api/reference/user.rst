User API
========

The User API can be used to retrieve public information about a user, and to
discover user-related resources.


Resources
---------

The User API defines the following resources ::

  /user/<username>


Get User Info
-------------

Request ::

    GET /user/<username>
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
            "subscriptions": "http://api.gpodder.net/stefan/subscriptions",
            ...
        }
    }

