.. _directory-api:

Directory API
=============

The Directory API can be used to discover podcasts.


Resources
---------

The Directory API defines the following resources ::

    /search/podcasts
    /directory/toplist
    /directory/tags/latest
    /directory/tag/<tag>


Podcast Toplist
---------------

Get the toplist ::

    GET /directory/toplist
    Content-Tpe: application/json


Response ::

    200 OK
    Content-Tpe: application/json

    TODO: body


Podcast Search
--------------

Parameters:

* **q**: query string (mandatory)


Request ::

    GET /search/podcasts?q=linux
    Content-Tpe: application/json


Response ::

    200 OK
    Content-Tpe: application/json

    TODO: body


Latest Tags
-----------

Parameters:

* **num**: number of tags to return (optional, default: 10)


Request ::

    GET /directory/tags/latest
    Content-Tpe: application/json


Response ::

    200 OK
    Content-Tpe: application/json

    TODO: body


Podcasts for Tag
----------------


Podcast Suggestions
-------------------


