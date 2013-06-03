.. _subscriptions-api:

Subscriptions API
=================

The subscriptions API is used to manage the podcast subscriptions of a client
device.


Resources
---------

The Subscriptions API defines the following resources ::

 /user/<username>/subscriptions
 /user/<username>/device/<device-id>/subscriptions


Subscription Upload
-------------------

Clients can upload the podcast subscriptions for a device to replace any
existing subscriptions.


Request
^^^^^^^

The client sends an object containing all current subscriptions for the
device. ::

 PUT /user/<username>/device/<device-id>/subscriptions
 Content-Type: application/json

 {
    podcasts: [
        { url: "http://example.com/podcast.rss" },
        { url: "http://podcast.com/episodes.xml" }
    ]
 }


Response
^^^^^^^^

The server can respond with the following status codes.

If a ``Link`` header with ``rel=changes`` is provided, this URL can be used to
retrieve changes to the subscriptions since the respective response (see
:ref:`subscription-change-download`)

If a new device has been created ::

 201 Created
 Link: <https://api.gpodder.net/user/<username>/device/<device-id>/subscription?since=0>; rel=changes

 no body


If the subscriptions have been processed immediatelly ::

 204 No Content
 Link: <https://api.gpodder.net/user/<username>/device/<device-id>/subscription?since=1234>; rel=changes

 no body


If the subscriptions have been accepted for later processing ::

 202 Accepted

 no body

No change download address is provided in this case, as is is not yet known at
the time of the response. If the client needs to know the current
subscriptions, it should follow up by a request to download the subscriptions.

If invalid podcast information is provided (eg an invalid feed URL), the whole
request will be rejected. ::

 400 Bad Request
 Content-Type: application/json

 {
   "message": "Invalid podcast URL",
   "errors": [
     {
       "field": "/podcasts/1",
       "code": "invalid_url"
     }
   ]
 }


Subscription Download
---------------------

Clients can download the current subscriptions of a device.


Request
^^^^^^^

Download subscriptions of a device ::

 GET /user/<username>/device/<device-id>/subscriptions
 Content-Type: application/json


Download all of the user's subscriptions ::

 GET /user/<username>/subscriptions
 Content-Type: application/json


Response
^^^^^^^^

The podcasts correspond to the :ref:`podcast-type` type. ::

 200 OK
 Link: <https://api.gpodder.net/user/<username>/device/<device-id>/subscription?since=1234>; rel=changes
 Content-Type: application/json

 {
    podcasts: [
        { podcast1 },
        { podcast2 }
    ]
 }

The changes link is not provided if all subscriptions of a user are requested.


Subscription Change Upload
--------------------------

Clients can update the current subscriptions of a device by reporting
subscribed and unsubscribed podcasts.


Request
^^^^^^^

A client can send which podcasts have been subscribed and unsubscribed. ::

 POST /user/<username>/device/<device-id>/subscriptions
 Content-Tpe: application/json

 {
    subscribe: [
        { url: "http://example.com/podcast.rss" }
    ]
    unsubscribe: [
        { url: "http://podcast.com/episodes.xml" }
    ]
 }

A client MUST NOT upload a change set where both ``subscribe`` and
``unsubscribe`` are empty.


Response
^^^^^^^^

The server responds with either of the following status codes.

The changes are processed immediatelly. ::

 200 OK
 Content-Tpe: application/json

 body according to Subscription Download


The changes have been accepted for later processing. ::

 204 Accepted

 no body

No response body is provided in this case, as it is not yet known.


.. _subscription-change-download:

Subscription Change Download
----------------------------

Download changes to the subscriptions of a device.


Request
^^^^^^^

The client makes the following request. ::

 GET /user/<username>/device/<device-id>/subscriptions?since=<since>
 Content-Tpe: application/json


Response
^^^^^^^^

The server can response with any of the following status codes.

The changes are returned immediatelly. ::

 200 OK
 Link: <https://api.gpodder.net/user/<username>/device/<device-id>/subscription?since=1234>; rel=changes
 Content-Type: application/json

 {
    subscribe: [
        { url: "http://example.com/podcast.rss" }
    ]
    unsubscribe: [
        { url: "http://podcast.com/episodes.xml" }
    ]
 }

The server can also return a prepared response (see
:ref:`prepared-response-api`).
