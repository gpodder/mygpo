General Information
===================

The API can be accessed via http and https. https is preferable from a security
/ privacy point of view and should be used by all clients. gpodder.net also
seems to be blocked in China via plain http.

All endpoints are offered at https://api.gpodder.net/3/.


* Request and Response Formats: JSON
* JSONP also available
* Date format: ISO 8601 / `RFC 3339 <http://tools.ietf.org/html/rfc3339>`_
  ``YYYY-MM-DDTHH:MM:SSZ``

Podcast is identified by its feed URL, episode is identified by its media URL.

TODO: see http://developer.github.com/v3/ for relevant information!


Status Codes
------------

The following status codes can be returned for any API request. Most resources
will, however, define additional status codes.

+----------------------------+-----------------------------------------------+
| Status Code                | Interpretation                                |
+============================+===============================================+
| 200 OK                     | All OK                                        |
+----------------------------+-----------------------------------------------+
| 301 Moved Permanently      | The resource has moved permanently to the     |
|                            | location provided in the Location header.     |
|                            | Subsequent requests should use the new        |
|                            | location directly.                            |
+----------------------------+-----------------------------------------------+
| 303 See Other              | the response to the request is found at the   |
|                            | location provided in the Location header. It  |
|                            | should be retrieved using a GET request       |
+----------------------------+-----------------------------------------------+
| 400 Bad Request            | invalid JSON, invalid types                   |
+----------------------------+-----------------------------------------------+
| 503 Service Unavailable    | The service and/or API are under maintenance  |
+----------------------------+-----------------------------------------------+

* Request not allowed (eg quota, authentication, permissions, etc)


Responses
---------

All responses are valid JSON (unless otherwise stated).


Error messages
--------------

The response could look like ::

    { message: "message", errors: [...] }

Errors could look like this ::

    {
        resource: "",
        field: "",
        code: ""
    }



Redirects
---------

permanent (301) vs temporary (302, 307) redirects.


Authentication
--------------

See Authentication API



Rate Limiting
-------------

See usage quotas ::

    GET /rate_limit

    HTTP/1.1 200 OK
    Status: 200 OK
    X-RateLimit-Limit: 60
    X-RateLimit-Remaining: 56

What counts as request? conditional requests?



Conditional Requests
--------------------

Some responses return ``Last-Modified`` and ``ETag`` headers. Clients SHOULD
use the values of these headers to make subsequent requests to those resources
using the ``If-Modified-Since`` and ``If-None-Match`` headers, respectively. If
the resource has not changed, the server will return a ``304 Not Modified``.
Making a conditional request and receiving a 304 response does not count
against the rate limit.


Formats
-------

All data is exchanged as `JSON <http://tools.ietf.org/html/rfc4627>`_. All
resources are represented as JSON objects, and requests are expected as also
expected to contain JSON objects.


JSONP Callbacks
^^^^^^^^^^^^^^^

You can pass a ``?callback=<function-name>`` parameter to any GET call to have
the results wrapped in a JSON function. This is typically used when browsers
want to embed content received from the API in web pages by getting around
cross domain issues. The response includes the same data output as the regular
API, plus the relevant HTTP Header information.
