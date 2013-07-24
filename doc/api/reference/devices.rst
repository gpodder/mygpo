.. _devices-api:

Devices API
===========

Devices are used throughout the API to identify a device / a client
application. A device ID can be any string matching the regular expression
``[\w.-]+``. The client application MUST generate a string to be used as its
device ID, and SHOULD ensure that it is unique within the user account. A good
approach is to combine the application name and the name of the host it is
running on.

The API maintains subscriptions per device ID. Two distinct devices using the
same ID might receive (from their point of view) incomplete information.  While
it is possible to retrieve a list of devices and their IDs from the server,
this SHOULD NOT be used to let a user select an existing device ID.

Each device has exactly one type, which can be either *desktop*, *laptop*,
*mobile*, *server* or *other*. When retrieving device information, clients
SHOULD map unknown device types to *other*. Clients MUST NOT send
different device types that those previously stated.


Resources
---------

The Devices API defines the following resources ::

    /user/{username}/devices
    /user/{username}/device/{device_id}


Retrieve Device List
--------------------

Retrieve the list of existing devices ::

    GET /user/{username}/devices
    Content-Type: application/json

    200 OK
    TODO: headers

    {
        "username": "username",
        "devices": [
            {
                "id": "mynotebook",
                "caption": "gPodder on my Notebook",
                "type": "laptop",
                "subscriptions": 10
            }
        ]
    }


Get Device Information
----------------------

Retrieve information about a specific device ::

    GET /user/{username}/device/{device_id}
    Content-Type: application/json

    200 OK
    TODO: headers

    {
        "id": "mynotebook",
        "caption": "gPodder on my Notebook",
        "type": "laptop",
        "subscriptions": 10
    }

404 is returned if no such device exists.


Update Device Information
-------------------------

Update the information of a device ::

    POST /user/{username}/device/{device_id}
    Content-Type: application/json

    TODO response: return device information

The body of the request MUST contain a JSON object that can contain the fields
*caption* and *type*. The information stored on the server will be updated with
the provided values. Fields not included in the request will not be updated.

If no device with the specified Id exists, a new device is created. Default
values are used for missing fields.
