.. _events-api:

Events API
==========

The **Events API** can be used by clients to exchange information about the
status of podcast episodes. Clients upload events with certain actions such as
*play* to inform other clients that an episode has already been played. Clients
can receive episode actions, for example on startup, to update the status of
episodes accordingly.


Resources
---------

The Events API defines the following resources ::

    /user/{username}/events
    /user/{username}/events/response/{id}
    /user/{username}/events/device/{device_id}


Event Data
----------

An event is a JSON object with the following attributes.

+--------------+----------+---------------------------------------------------+
| Attribute    | Required | Values                                            |
+==============+==========+===================================================+
| action       | yes      | one of ``play``, ``download``, ``flattr``,        |
|              |          | ``delete``                                        |
+--------------+----------+---------------------------------------------------+
| timestamp    | yes      | The UTC timestamp at which the event occured as   |
|              |          | `RFC 3339 <http://www.ietf.org/rfc/rfc3339.txt>`_ |
+--------------+----------+---------------------------------------------------+
| podcast      | yes      | The feed URL of the podcast                       |
+--------------+----------+---------------------------------------------------+
| episode      | yes      | The media URL of the episode                      |
+--------------+----------+---------------------------------------------------+
| device       | no       | The device ID at which the event was triggered    |
+--------------+----------+---------------------------------------------------+
| started      | no       | The position (in seconds) at which a play event   |
|              |          | started                                           |
+--------------+----------+---------------------------------------------------+
| positon      | no       | The position (in seconds) at which a play event   |
|              |          | was stopped                                       |
+--------------+----------+---------------------------------------------------+
| total        | no       | The total duratin (in seconds) of the media file  |
+--------------+----------+---------------------------------------------------+


Event Types
^^^^^^^^^^^

The following types of events (*actions*) are currently defined.

* *play*: the episode has been played
* *download*: the episode has been downloaded
* *flattr*: the episode has been flattered
* *delete*: the episode has been deleted

Additional event types might be defined in the future. To ensure forward
compatability, clients should accept (in if necessary ignore) events of unknown
type.


Upload Events
-------------

Clients can upload new events to gpodder.net to make them available online and
for other clients. Clients MUST NOT upload events that have not been triggered
through them (ie events that have been donwloaded from the API).

Clients SHOULD aggregate events in upload them in batches.


Request
^^^^^^^

To initiate an upload, the following request should be issued. ::

    POST /user/{username}/events
    Content-Tpe: application/json

    {
        events: [
            { event },
            { event },
            ...
        ]
    }

Clients MUST NOT upload an empty list of events.

TODO: add ``default_data`` attribute to object, to avoid repeating the same
data over and over?

Clients MUST NOT upload invalid event objects.

If events reference devices that do not yet exist, they are automatically
created with default data.

TODO: specify device-id at top-level? what about events that don't belong to
any device? move device-id to URL?


Response
^^^^^^^^

The following responses are possible.

The uploaded list of events has been processed immediatelly ::

    204 No Content


The uploaded list of events has been accepted for later processing ::

    202 Accepted


TODO: Validation?


Data
^^^^

No payload data is returned as a response to uploading events.


Download Events
---------------

Clients can download events to retrieve those that have been uploaded by other
devices (or itself) since a certain timestamp.

It is RECOMMENDED that clients do not persistently store events after they have
been uploaded. Instead they SHOULD download events after an upload, to retrieve
all events that they (and other clients) have uploaded.


Requests
^^^^^^^^

Download requests retrieve events that have been uploaded since a specific
timestamp. This timestamp can be given explicitly (if the corresponding
timestamp value is maintained) is implicitly by the device-id (the
server maintains a timestamp per device).

**Explicit Timestamp:** retrieve all events after a specific timestamp. ::

    GET /user/{username}/events{?since}

Parameters

* since: numeric timestamp value (mandatory)


**Implicit Timestamp:** retrieve all events that the current device has not yet
seen. The timestamp of is stored on the server side. ::

    GET /user/{username}/device/{device_id}/events

Parameters

* reset: can be set to true to reset the server-side timestamp to 0 and
  retrieve all events.


Responses
^^^^^^^^^

Response ::

    200 OK
    Content-Tpe: application/json
    TODO ...?

    {
        since: ...,
        timestamp: ...,
        events: [
            { event },
            { event },
            ...
        ]
    }


The server can also return a prepared response (see
:ref:`prepared-response-api`).

A successful response indicates a timeframe (between ``since`` and
``timestamp``) for which events have been retrieved. When using
*explicit* queries, the client MUST use the value of the last respone's
``timestamp`` field as the value of the ``since`` parameter in the following
request. The ``since`` paramter can be set to ``0`` if previously retrieved
events have been lost (eg through a database reset). This MUST, however, be an
exceptional case.


Data
^^^^

The client can expect the retrieved events to be well-formed but SHOULD be able
to at least safely ignore invalid events. This includes events with an
``action`` which is not listed above. While the API does perform input
validation on uploaded events, this should ensure that clients are able to
remain operational if for example new event types are introduced which have
different requirements to the provided attributes.
