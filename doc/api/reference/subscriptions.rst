.. _subscriptions-api:

Subscriptions API
=================

The subscriptions API is used to manage the podcast subscriptions of a client
device.


Resources
---------

The Subscriptions API defines the following resources ::

 /user/{username}/subscriptions
 /user/{username}/device/{deviceid}/subscriptions

The first resource represents the summary of subscriptions over all devices. It
can not be modified directly.

The second resource represents the subscriptions of a single
:ref:`device-integration`.


Subscription Upload
-------------------

Clients can upload the podcast subscriptions for a :ref:`device-integration` to
replace its existing subscriptions.


Request
^^^^^^^

The client sends an object containing all current subscriptions for the
device. ::

 PUT /user/{username}/device/{deviceid}/subscriptions
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
 Link: <https://api.gpodder.net/user/{username}/device/{deviceid}/subscription?since=0>; rel=changes

 no body


If the subscriptions have been processed immediatelly ::

 204 No Content
 Link: <https://api.gpodder.net/user/{username}/device/{deviceid}/subscription?since=1234>; rel=changes

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

Clients can download the current subscriptions either of a single
:ref:`device-integration` or over all of the user's devices.


Request
^^^^^^^

Download subscriptions of a device ::

 GET /user/{username}/device/{deviceid}/subscriptions
 Content-Type: application/json


Download all of the user's subscriptions ::

 GET /user/{username}/subscriptions
 Content-Type: application/json


Response
^^^^^^^^

The podcasts correspond to the :ref:`podcast-type` type. ::

 200 OK
 Link: <https://api.gpodder.net/user/{username}/device/{deviceid}/subscription?since=1234>; rel=changes
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

Clients can update the current subscriptions of a :ref:`device-integration` by
reporting subscribed and unsubscribed podcasts.


Request
^^^^^^^

A client can send which podcasts have been subscribed and unsubscribed. ::

 POST /user/{username}/device/{deviceid}/subscriptions
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
``unsubscribe`` are empty, or where the same podcast is given in both
``subscribe`` and ``unsubscribe``.


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

Download changes to the subscriptions of a :ref:`device-integration`.


Request
^^^^^^^

The client makes the following request. ::

 GET /user/{username}/device/{deviceid}/subscriptions{?since}
 Content-Tpe: application/json


Response
^^^^^^^^

The server can response with any of the following status codes.

The changes are returned immediatelly. ::

 200 OK
 Link: <https://api.gpodder.net/user/{username}/device/{deviceid}/subscription?since=1234>; rel=changes
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


Integration Recommendations
---------------------------

This section describes how the API can be accessed for common use cases.

* On first startup a client CAN retrieve the list of all the user's
  subscriptions to offer as suggestions.

* On first startup a client SHOULD generate a unique :ref:`device-integration`
  Id for managing its own subscriptions in subsequent API calls.

* A client which has been somehow "reset" can re-use an existing device ID and
  restore its subscriptions from there. It SHOULD NOT share the same device ID
  with another installation which is still used.

* A client SHOULD either use the combination of Subscription Upload and
  Download endpoints, or the Subscription Change endpoints to keep its
  subscriptions up to date.

* When retrieving subscriptions or subscription changes, a client SHOULD use
  the URL in the ``Link`` header with ``rel=changes`` (if present) to retrieve
  subsequent changes to the resource.
