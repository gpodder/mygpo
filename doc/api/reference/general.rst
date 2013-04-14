General Information
===================

The API can be accessed via http and https. https is preferable from a security
/ privacy point of view and should be used by all clients. gpodder.net also
seems to be blocked in China via plain http.

All endpoints are offered at https://api.gpodder.net/3/.


Podcast is identified by its feed URL, episode is identified by its media URL.

TODO: see http://developer.github.com/v3/ for relevant information!


Status Codes
------------

The API uses the following status codes

+----------------------------+-----------------------------------------------+
| Status Code                | Interpretation                                |
+============================+===============================================+
| 200 OK                     | All OK                                        |
+----------------------------+-----------------------------------------------+
| 503 Service Unavailable    | The service and/or API are under maintenance  |
+----------------------------+-----------------------------------------------+

* Request not allowed (eg quota, authentication, permissions, etc)


Responses
---------

All responses are valid JSON (unless otherwise stated).
