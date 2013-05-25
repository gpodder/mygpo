.. _prepared-response-api:

Prepared Response API
=====================

This API is used by other parts of the API. It is not supposed to be initiated
by clients directly.

Some requests might require the server to prepare a response. This process can
take longer than common request timeouts.

In such cases, the server will provide a URL from which the response can be
retrieved.


Resources
---------

The Prepared Response API defines the following resources ::

 /response/<id>


Prepared Responses
------------------

The server can indicate a prepared response in the following way. ::

    303 See Other
    Link: /response/<id>

Please note that any URL might be used in the ``Link`` header.

The server is preparing the result at the specified resource. The client should
try to fetch the data from the given URLs. ::

    GET /response/<id>
    Content-Tpe: application/json


A status code 404 is returned before the data is ready. The client may retry
after the given number of seconds. ::

    404 Not Found
    Retry-After: 120


When the data is ready, 200 will be returned ::

    200 OK
    Content-Tpe: application/json

    body

When the data is no longer available, a 410 is returned. ::

    410 Gone

In this case the client SHOULD retry the previous request.
