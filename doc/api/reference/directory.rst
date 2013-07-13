.. _directory-api:

Directory API
=============

The Directory API can be used to discover podcasts.

TODO: report problems with podcasts (eg duplicates, missing data)


Resources
---------

The Directory API defines the following resources ::

    /search/podcasts
    /directory/toplist
    /directory/tags/latest
    /directory/tag/{tag}
    /user/{username}/suggestions


Podcast Toplist
---------------

The podcast toplist ranks podcasts by their number of subscribers.


Parameters
^^^^^^^^^^

* **lang**: a ISO 639-1 (two-letter) language code. If given, only podcasts in
  this language are returned. If omitted, no language restriction is made.

Request
^^^^^^^

Get the toplist ::

    GET /directory/toplist{?lang:2}
    Content-Tpe: application/json


Response
^^^^^^^^

The response contains a ``toplist`` member which has a list of
:ref:`podcast-type` objects. The first entry in the list represents the highest
ranking podcast in the toplist. If a ``lang`` parameter was included in the
request, it is also included in the response. ::

    200 OK
    Content-Tpe: application/json

    {
        "toplist": [
            podcast1,
            podcast2,
            podcast3,
            ...
        ],
        "lang": "en"
    }


Podcast Search
--------------

Parameters
^^^^^^^^^^

* **q**: query string (mandatory)


Request
^^^^^^^

The search query is provided as a GET parameter. ::

    GET /search/podcasts{?q}
    Content-Tpe: application/json


Responses
^^^^^^^^^

If the search could be performed, the search results (if any) are returned in
the ``search`` member. The query is returned in the ``query`` member. ::

    200 OK
    Content-Type: application/json

    {
        "search": [
            podcast1,
            podcast2,
            ...
        ],
        "query": "query text"
    }


If the search could not be performed, for example because the query was
missing ::

    400 Bad Request
    Content-Type: application/json

    {
        "message": "parameter q missing",
        "errors": [
            {
                field: "?q",
                code: "parameter_missing"
            }
        ]
    }


Example
^^^^^^^

Example::

    GET /search/podcasts?q=linux
    Content-Tpe: application/json


    200 OK
    Content-Tpe: application/json

    {
        "search": [
            { "url": "http://example.com/feed.rss", ...},
            { ... },
            ...
        ],
        "query": "linux"
    }



Latest Tags
-----------

The "Latest Tags" endpoint returns *current* tags. Those are tags for which
podcasts have recently published a new episode.

Parameters
^^^^^^^^^^

* **num**: number of tags to return (optional, default: 10)


Request
^^^^^^^

The number of tags to return can be included in the request. ::

    GET /directory/tags/latest{?num}
    Content-Tpe: application/json


Reponse
^^^^^^^

In the ``tags`` member a list of :ref:`tag-type` objects is provided. ::

    200 OK
    Content-Tpe: application/json
    Link: <https://api.gpodder.net/3/directory/tag/{label}>; rel="https://api.gpodder.net/3/relation/tag-podcasts"; title="Podcasts for tag {label}"

    {
        "tags": [
            { "label": "Technology" },
            { ... },
            ...
        ]
    }

Clients can use the provided ``Link`` header and resolve the `URI template
<http://tools.ietf.org/html/rfc6570>`_ to obtain the URL for retrieving the
podcasts of a certain tag.


Podcasts for Tag
----------------

Clients can retrieve podcasts for a given tag.


Request
^^^^^^^

Request. ::

    GET /directory/tag/{tag}
    Content-Tpe: application/json


Response
^^^^^^^^

Response. ::

    200 OK
    Content-Tpe: application/json

    TODO: body


Podcast Suggestions
-------------------

Clients can retrieve suggested podcasts for the current user.


Request
^^^^^^^

Request. ::

    GET /user/{username}/suggestions
    Content-Tpe: application/json



Response
^^^^^^^^

The response contains a ``suggestions`` member which has a list of
:ref:`podcast-type` objects. ::

    200 OK
    Content-Tpe: application/json

    {
        "suggestions": [
            { podcast1 },
            { podcast2 },
            ...
        ]
    }
