General Information
===================

The API can be accessed via http and https. https is preferable from a security
/ privacy point of view and should be used by all clients. gpodder.net also
seems to be blocked in China via plain http.

All endpoints are relative to https://api.gpodder.net/3/.


* Request and Response Formats: JSON
* JSONP also available
* Date format: ISO 8601 / `RFC 3339 <http://tools.ietf.org/html/rfc3339>`_
  ``YYYY-MM-DDTHH:MM:SSZ``

Podcast is identified by its feed URL, episode is identified by its media URL.

TODO: see http://developer.github.com/v3/ for relevant information!

TODO: see `URI Templates <http://tools.ietf.org/html/rfc6570>`_


Status Codes
------------

The API uses HTTP status codes to inform clients about type of response. The
semantics are used according to `their specified semantics
<http://www.iana.org/assignments/http-status-codes/>`_.

The specification of each API endpoint describes which status codes should be
expected. In addition the following status codes can be returned for any API
request.

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

TODO: review `Problem Details for HTTP APIs
<http://tools.ietf.org/html/draft-nottingham-http-problem>`_

An error response looks like ::

    { message: "message", errors: [...] }

The ``errors`` array contains objects with the following information ::

    {
        field: "<JSON Pointer to field>",
        code: "<error code>"
    }

The ``field`` value indicates where the error occured.

* If the value starts with a ``/``, it should be interpreted as a `JSON Pointer
  <http://tools.ietf.org/html/rfc6901>`_ to the problematic field in the
  request body.

* If the value starts with a ``?``, it is followed by the name of the parameter
  that was responsible for the error.

* The value can be null, indicating that the error was not caused by a specific
  field.

The ``code`` describes the actual error. The following error codes are defined:

* ``ìnvalid_url``: The provided values is not a valid URL.
* ``parameter_missing``: A mandatory parameter was not provided.

Error codes may be added on demand. Clients should therefore expect and accept
arbitrary string values.


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


Resource Types
--------------

.. _podcast-type:

Podcast
^^^^^^^

A podcast is represented as a JSON object containing at least an ``url``
member. ::

    {
        url: "http://example.com/podcast.rss",
        title: "Cool Podcast",
        logo: "http://example.com/podcast-logo.png"
    }


.. _tag-type:

Tag
^^^

A tag is represented as a JSON object containing at least a ``label``
member. ::

    {
        "label": "Technology"
    }


Relations
---------

`Relation types <http://tools.ietf.org/html/rfc5988#section-5.3>`_ that are
used in the API:

* ``https://api.gpodder.net/3/relation/tag-podcasts``: podcasts for a given tag

TODO: should they be on domain api.gpodder.net, or just gpodder.net?
