.. _events-api:

Events API
==========


Resources
---------

The Events API defines the following resources ::

    /user/<username>/events
    /user/<username>/events/<id>


Upload Events
-------------

Request ::

    POST /user/<username>/events
    Content-Tpe: application/json


Responses:

Processed immediatelly ::

    204 No Content


Accepted for later processing ::

    202 Accepted



Download Events
---------------

Parameters

* since (optional, default 0)


Request ::

    GET /user/<username>/events


Responses.

Response ::

    200 OK
    Content-Tpe: application/json
    TODO ...?


Response is being prepared ::

    203 Found / 202 See Other
    Link: /user/<username>/events/<id>


The server is preparing the result at the specified resource. The client should
try to fetch the data from the given URLs. ::

    GET /user/<username>/events/<id>
    Content-Tpe: application/json


A 404 might be returned before the data is ready. The client may retry after
xxx seconds. ::

    404 Not Found


When the data is ready, 200 will be returned ::

    200 OK
    Content-Tpe: application/json

    TODO: body...


When the data is no longer available, a 410 is returned. ::

    410 Gone


