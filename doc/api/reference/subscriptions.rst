.. _subscriptions-api:

Subscriptions API
=================

The subscriptions API is used to manage the podcast subscriptions of a client
device.

TODO: what to do with not-accepted (invalid) podcasts (eg feed URLs that are
invalid URLs)?


Resources
---------

The Subscriptions API defines the following resources ::

 /user/<username>/subscriptions
 /user/<username>/device/<device-id>/subscriptions


Subscription Upload
-------------------

Upload the subscriptions for a device ::

 PUT /user/<username>/device/<device-id>/subscriptions
 Content-Tpe: application/json

 TODO: specify body


The server can respond with the following status codes.

When a new device has been created ::

 201 Created
 Link: <https://api.gpodder.net/user/<username>/device/<device-id>/subscription?since=0>; rel=changes
 ...


When the subscriptions have been processed immediatelly ::

 204 No Content
 Link: <https://api.gpodder.net/user/<username>/device/<device-id>/subscription?since=1234>; rel=changes
 ...


When the subscriptions have been accepted for later processing ::

 202 Accepted
 Link: <https://api.gpodder.net/user/<username>/device/<device-id>/subscription?since=1234>; rel=changes
 ...
 TODO: return change download address here?


Any status code >= 200 and < 300 should be considered a success.

TODO: specify body?


Subscription Download
---------------------

Download subscriptions of a device ::

 GET /user/<username>/device/<device-id>/subscriptions
 Content-Type: application/json

 200 Found
 Link: <https://api.gpodder.net/user/<username>/device/<device-id>/subscription?since=1234>; rel=changes
 Content-Type: application/json
 Last-Modified: ...

 {
     "add": [{ "url": "..."}, { ...}]
     "timestamp": 1234,
 }


Download all of the users subscriptions ::

 GET /user/<username>/subscriptions
 Content-Type: application/json

 200 Found
 Link: <https://api.gpodder.net/user/<username>/device/<device-id>/subscription?since=1234>; rel=changes
 Content-Type: application/json
 Last-Modified: ...

 TODO: specify body


Subscription Change Upload
--------------------------

Upload changes to the subscriptions of a device ::

 POST /user/<username>/device/<device-id>/subscriptions
 Content-Tpe: application/json

 TODO: specify body...



Subscription Change Download
----------------------------

Download changes to the subscriptions of a device ::

 GET /user/<username>/device/<device-id>/subscriptions?since=<since>
 Content-Tpe: application/json

 200 Found
 Link: <https://api.gpodder.net/user/<username>/device/<device-id>/subscription?since=1234>; rel=changes
 Content-Type: application/json
 Last-Modified: ...

 TODO: specify body...


