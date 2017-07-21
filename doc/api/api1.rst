.. _api1:


API 1 (Deprecated)
==================

This page describes version 1 of the gpodder.net API which is deprecated in
favor of version 2.


There are two different APIs for different target audiences:

* The Simple API targets developers who want to write quick integration into
  their existing applications
* The Advanced API targets developers who want tight integration into their
  applications (with more features)


Reference Implementation
------------------------

https://github.com/gpodder/mygpoclient


Legacy API
----------

This API is for support of old clients (gPodder 2.1 and earlier) and should
never be used in new code. It's just here for reference of what the server
implementation should provide.

upload
^^^^^^

* Request URI: ``/upload`` * Parameters: ``username`` (the e-mail address of
  the user), ``password`` (the user password in plaintext), ``action`` (always
  set to ``update-subscriptions``), ``protocol`` (always set to ``0``),
  ``opml`` (a HTTP file upload field that contains the subscription list as
  OPML file)

Parses the given OPML file and compares the user's default subscription list
with the entries from the OPML file. For every new subscription, the server
automatically creates a "subscribe" event, and for every removed subscription,
the server automatically generates a "unsubscribe" event. The user's default
subscription list on the server will match the uploaded OPML file after the
request returns ``@SUCCESS``.

Possible response values (these are potentially contained within surrounding
text, e.g. HTML):

* ``@GOTOMYGPODDER``: The website it opened in the web browser and the user
  gets the message "Please have a look at the website for more information."
* ``@SUCCESS``: The subscription has been successfully uploaded.
* ``@AUTHFAIL``: The supplied username and password combination is wrong.
* ``@PROTOERROR``: There has been an error in the request format (wrong OPML
  format, wrong parameters, etc..).
* ''None of the above'': This is an "unknown" response, and the client displays
  an error message to the user.

getlist
^^^^^^^

* Request URI: ``/getlist``
* Parameters: ``username`` (the e-mail address of the user), ``password`` (the
  user password in plaintext)

This returns the main subscription list of the user as OPML content.

register
^^^^^^^^

* Request URI: ``/register``
* Parameters: None

This web page is to be opened in a web browser if the user choses to create a
new user account.


toplist.opml
^^^^^^^^^^^^

* Request URI: ``/toplist.opml``
* Parameters: None

This should return an OPML file with the top 50 podcasts. This is the same as
the Simple API endpoint ``/toplist/50.opml`` and can (obviously) utilize the
same code.


Simple API
----------

The Simple API provides a way to upload and download subscription lists in
bulk. This allows developers of podcast-related applications to quickly
integrate support for the web service, as the only

* Synchronization of episode status fields is ``not`` supported
* This API uses more bandwith than the advanced API
* The client can be stateless
* The client can be low-powered - subscribe/unsubscribe events are calculated
  on the server-side

Downloading subscription lists
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Request: ``GET /subscriptions/''{username}''/''{device_id}''.opml``
* Request: ``GET /subscriptions/''{username}''/''{device_id}''.json``
* Request: ``GET /subscriptions/''{username}''/''{device_id}''.txt``
* Requires HTTP authentication

Get a list of subscribed podcasts for the given user. The first variant returns
the content as OPML feed, the second variant as list of feed URLs in JSON
format. The third variant returns the list of URLs (one per line) as simple
plaintext.

* Example: ``GET /subscriptions/bob/asdf.opml`` (Download bob's list for
  device ID ``asdf`` as OPML)

In case of errors, the following HTTP status codes are used:

* ``401`` Invalid user
* ``404`` Invalid device ID
* ``400`` Invalid format (e.g. broken OPML)

Uploading subscription lists
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Request: ``PUT /subscriptions/''{username}''/''{device_id}''.opml``
* Request: ``PUT /subscriptions/''{username}''/''{device_id}''.json``
* Request: ``PUT /subscriptions/''{username}''/''{device_id}''.txt``
* Requires HTTP authentication

Upload the current subscription list of the given user to the server. The data
should be provided either in OPML, JSON or plaintext (one URL per line) format,
and should be uploaded just like a normal PUT request (i.e. in the body
of the request).

For successful updates, the implementation ``always`` returns the status code
``200`` and the ''empty string'' (i.e. an empty HTTP body) as a result, any
other string should be interpreted by the client as an (undefined) error.

Defined errors are as follows (in this case, the body that is received from the
server ''might'' be a user-friendy description of the error):

* ``401`` Invalid user
* ``400`` Invalid format (cannot parse OPML or JSON)

In case the device does not exist for the given user, it is automatically
created. If clients want to determine if a device exists, you have to to a GET
request on the same URL first and check for a the 404 status code (see above).

* Example: ``PUT /subscriptions/john/e9c4ea4ae004efac40.txt`` (Upload john's
  list for that device as text file)


Downloading podcast toplists
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Request: ``GET /toplist/''{number}''.opml``
* Request: ``GET /toplist/''{number}''.json``
* Request: ``GET /toplist/''{number}''.txt``
* Does ''not'' require authentication (''public content'')

The ``number`` field might be any value in the range 1..100 (inclusive both
boundaries). An example request looks like:

* ``GET /toplist/50.json`` - Get the top 50 list in JSON format

Download a list of podcasts, sorted in descending order (more popular podcasts
first) in different formats. The OPML and TXT formats do not add any
information about the (absolute and relative) popularity for each podcast, only
the ordering can be considered. The JSON format includes a more detailed list,
usable for clients that want to display a detailed toplist or post-process
the toplist:


.. code-block:: json

     [{"url": "http://twit.tv/node/4350/feed",
       "title": "FLOSS Weekly",
       "description": "Free, Libre and Open Source Software with Leo.",
       "subscribers": 4711,
       "subscribers_last_week": 4700
      },
      {"url": "http://feeds.feedburner.com/LinuxOutlaws",
       "title": "The Linux Outlaws",
       "description": "A podcast about Linux with Dan and Fab.",
       "subscribers": 1337,
       "subscribers_last_week": 1330,
      }]

All shown keys must be provided by the server. The ``description`` field may be
set to the empty string in case a description is not available. The ``title``
field may be set to the URL in case a title is not available. The
``subscribers_last_week`` field may be set to zero if no data is available. The
client can use the ``subscribers_last_week`` counts to re-sort the list and get
a ranking for the last week. With this information, a relative "position
movement" can also be calculated if the developer of the client decides to do
so.

Downloading podcast suggestions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Request: ``GET /suggestions/''{number}''.opml``
* Request: ``GET /suggestions/''{number}''.json``
* Request: ``GET /suggestions/''{number}''.txt``
* Requires HTTP authentication

The ``number`` field might be any value in the range 1..100 (inclusive both
boundaries). An example request looks like:

* ``GET /suggestions/10.opml`` - Get 10 suggestions in OPML format

Download a list of podcasts that the user has not yet subscribed to (by
checking ''all'' server-side subscription lists) and that might be
interesting to the user based on existing subscriptions (again on ''all''
server-side subscription lists).

The TXT format is a simple URL list (one URL per line), and the OPML file is a
"standard" OPML feed. The JSON format looks as follows:


.. code-block:: json

     [{"url": "http://twit.tv/node/4350/feed",
       "title": "FLOSS Weekly",
       "description": "Free, Libre and Open Source Software with Leo."
      },
      {"url": "http://feeds.feedburner.com/LinuxOutlaws",
       "title": "The Linux Outlaws",
       "description": "A podcast about Linux with Dan and Fab."
      }]

The server does not specify the "relevance" for the podcast suggestion, and the client application ''SHOULD'' filter out any podcasts that are already added to the client application but that the server does not know about yet (although this is just a suggestion for a good client-side UX).


Searching for podcasts
^^^^^^^^^^^^^^^^^^^^^^

* Request: ``GET /search.opml?q=''{query}``''
* Request: ``GET /search.json?q=''{query}``''
* Request: ``GET /search.txt?q=''{query}``''
* Does ''not'' require authentication (''public content'')

Carries out a service-wide search for podcasts that match the given query.
Returns a list of podcasts.

The format of the search results is the same as for podcast suggestions. See
there for the exact format.


Advanced API
------------

The Advanced API provides more flexibility and enhanced functionality for
applications that want a tighter integration with the web service. A reference
implementation will be provided as part of the gPodder source code (and gPodder
will make use of that reference implementation).

* The client has to persist the synchronization state locally
* Only changes to subscriptions are uploaded and downloaded
* Synchronization of episode status fields is supported in this API
* Only JSON is used as the data format to ease development

Add/remove subscriptions
^^^^^^^^^^^^^^^^^^^^^^^^

* Request: ``POST /api/1/subscriptions/''{username}''/''{device_id}''.json``
* Requires HTTP authentication

Update the subscription list for a given device. Only deltas are supported
here. Timestamps are not supported, and are issued by the server.

Example JSON upload data:


.. code-block:: json

      {"add": ["http://example.com/feed.rss", "http://example.org/podcast.php"],
       "remove": ["http://example.net/foo.xml"]}

The server returns a timestamp/ID that can be used for requesting changes since
this upload in a subsequent API call (see below):


.. code-block:: json

  {"timestamp": 12345, "update_urls": []}

``Update 2010-01-07:`` In addition, the server MUST send any URLs that have
been rewritten (sanitized, see [[bug:747]]) as a list of tuples with the key
"update_urls". The client SHOULD parse this list and update the local
subscription list accordingly (the server only sanitizes the URL, so the
semantic "content" should stay the same and therefore the client can
simply update the URL value locally and use it for future updates. An
example result with update_urls:


.. code-block:: json

  {"timestamp": 1337,
   "update_urls": [
    ["http://feeds2.feedburner.com/LinuxOutlaws?format=xml",
     "http://feeds.feedburner.com/LinuxOutlaws"],
    ["http://example.org/podcast.rss ",
     "http://example.org/podcast.rss"]]}

``Update 2010-01-17:`` URLs that are not allowed (currently all URLs that don't
start with either http or https) are rewritten to the empty string and are
ignored by the Webservice.


Retrieving subscription changes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Request: ``GET /api/1/subscriptions/''{username}''/''{device_id}''.json?since=''{timestamp}``''
* Requires HTTP authentication

This API call retrieves only the changes since the last upload (the last upload
is determined by the "since" parameter, which usually is taken from the
return value of a previous update call). The response format is the
same as the upload format, i.e. JSON: A dictionary with two keys "add" and
"remove" where the value for each key is a list of URLs that should be added or
removed. There is one additional key ("timestamp") that is provided by the
server that will tell the client the next value for the "since" parameter in
case the client wants to issue another GET request in the future without
uploading data.

In case nothing has changed, the server returns something like the following
JSON content (in this case, the client SHOULD store the timestamp and use it
for future requests):


.. code-block:: json

      {"add": [], "remove": [], "timestamp": 12347}


Uploading episode actions
^^^^^^^^^^^^^^^^^^^^^^^^^

* Request: ``POST /api/1/episodes/''{username}''.json``
* Requires HTTP authentication

Upload changed episode actions. As actions are saved on a per-user basis (not
per-device), the API endpoint is the same for every device. For logging
purposes, the client can send the device ID to the server, so it appears in the
episode action log on the website.

Example JSON upload data:


.. code-block:: json

  [{"podcast": "http://example.com/feed.rss",
    "episode": "http://example.com/files/s01e20.mp3",
    "device": "gpodder_abcdef123",
    "action": "download",
    "timestamp": "2009-12-12T09:00:00"},
   {"podcast": "http://example.org/podcast.php",
    "episode": "http://ftp.example.org/foo.ogg",
    "action": "play",
    "position": "01:00:00"}]

Possible keys:

* ``podcast`` (required): The URL to the podcast feed the episode belongs to
* ``episode`` (required): The download URL/GUID of the episode
* ``device`` (optional): The device ID on which the action has taken place
* ``action`` (required): One of: download, play, delete, new
* ``timestamp`` (optional): An optional timestamp when the action took place,
  in [http://en.wikipedia.org/wiki/ISO_8601 ISO 8601 format] -
  **The timestamp MUST be in the UTC time zone**
* ``position`` (optional): Only valid for "play": the current play position
  in ``HH:MM:SS`` format

The return value is a JSON dictionary containing the timestamp (that can be
used for retrieving changed episode actions later on):


.. code-block:: json

    {"timestamp": 12345,
     "update_urls": [] }

The client SHOULD save this timestamp if it wants to retrieve episode actions
in the future in order to save bandwith and CPU time on the server.


``Update 2010-02-23:`` In addition, the server MUST send any URLs that have
been rewritten (sanitized, see [[bug:747]] and [[bug:862]]) as a list of tuples
with the key "update_urls". The client SHOULD parse this list and update the
local subscription and episode list accordingly (the server only sanitizes the
URL, so the semantic "content" should stay the same and therefore the
client can simply update the URL value locally and use it for future
updates. An example result with update_urls:


.. code-block:: json

  {"timestamp": 1337,
   "update_urls": [
    ["http://feeds2.feedburner.com/LinuxOutlaws?format=xml",
     "http://feeds.feedburner.com/LinuxOutlaws"],
    ["http://example.org/episode.mp3 ",
     "http://example.org/episode.mp3"]]}

URLs that are not allowed (currently all URLs that contain non-ASCII characters
    or don't start with either http or https) are rewritten to the empty string
and are ignored by the Webservice.


Retrieving episode actions
^^^^^^^^^^^^^^^^^^^^^^^^^^

* Request: ``GET /api/1/episodes/''{username}''.json``
* Request: ``GET /api/1/episodes/''{username}''.json?podcast=''{url}``''
* Request: ``GET /api/1/episodes/''{username}''.json?device=''{device-id}``''
* Request: ``GET /api/1/episodes/''{username}''.json?since=''{timestamp}``''
* Request: ``GET /api/1/episodes/''{username}''.json?podcast=''{url}''&since=''{timestamp}``''
* Request: ``GET /api/1/episodes/''{username}''.json?device=''{device-id}''&since=''{timestamp}``''
* Requires HTTP authentication

Download changed episode actions. The result is a list of all new episode
actions since the given timestamp. The timestamp is the value returned by the
episode upload request. The first three variants (without the "since"
parameter) downloads ALL episode actions for the given user. Please
note that this could be a potentially long list of episode actions, so clients
SHOULD prefer the "since" variants whenever possible (e.g. when uploads have
been taken place before).

The format of the action list is the same as with the action upload request,
but the format is a bit different so that the server can send the new
timestamp (that the client SHOULD save and use for subsequent requests):


.. code-block:: json

    {"actions": ''(list of episode actions here - see above for details)'',
     "timestamp": 12345}


There are two additional variants that take either a podcast URL or a device ID
and returns only episode actions related to the given podcast or device. In the
case of the device ID, all podcasts to which the device is currently subscribe
to, are combined, and episode actions for these are added.

''Client implementation notes:'' A client can make use of the device variant of
this request when it is assigned a single device id. When adding a podcast to
the client (without synching the subscription list straight away), the variant
with the podcast URL can be used. The first variant (no parameters at all) can
be used as a kind of "burst" download of all episode actions, but should be
used as little as possible (e.g. after a re-install, although even then, the
device-id parameter could be more useful).

(Re)naming devices and setting the type
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Request: ``POST /api/1/devices/''{username}''/''{device-id}''.json``
* Requires HTTP authentication

Set a new name for the device ID. The device ID is normally generated by the
client application, but for viewing the device on the web and for managing
subscriptions, it's easier to provide a "human-readable" name. The client
application should do this using this API call. It can also provide the type of
device, so that a special icon can be shown in the web UI. Only the keys that
are supplied will be updated.


.. code-block:: json

  {"caption": "gPodder on my Lappy", "type": "laptop"}

Possible keys:

* ``caption``: The new label for the device
* ``type``: The type of the device. (Possible values: desktop, laptop, mobile,
  server, other)


Getting a list of devices
^^^^^^^^^^^^^^^^^^^^^^^^^

* Request: ``GET /api/1/devices/''{username}''.json``
* Requires HTTP authentication

Returns the list of devices that belong to a user. This can be used by the
client to let the user select a device from which to retrieve subscriptions,
etc..


.. code-block:: json

  [{"id": "abcdef",
    "caption": "gPodder on my Lappy",
    "type": "laptop",
    "subscriptions": 27},
   {"id": "09jc23caf",
    "caption": "",
    "type": "other",
    "subscriptions": 30},
   {"id": "phone-au90f923023.203f9j23f",
    "caption": "My Phone",
    "type": "mobile",
    "subscriptions": 5}]

