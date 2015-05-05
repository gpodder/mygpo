General Information
===================

Protocol
--------

The API is provided via https. Requests via http will redirect to the
corresponding URL via https.

CORS
----

All endpoints send the `Access-Control-Allow-Origin: *
<http://www.w3.org/TR/cors/>`_ header which `allows web application to access
the API <http://enable-cors.org/>`_.


Identifying Podcasts and Episodes
---------------------------------

Podcast is identified by its feed URL, episode is identified by its media URL.


Date Format
-----------

Date format: ISO 8601 / `RFC 3339 <http://tools.ietf.org/html/rfc3339>`_:
``YYYY-MM-DDTHH:MM:SSZ``


.. _formats:

Formats
-------

All data is exchanged as `JSON <http://tools.ietf.org/html/rfc4627>`_. All
resources are represented as JSON objects, and requests are expected as also
expected to contain JSON objects.


JSONP Callbacks
^^^^^^^^^^^^^^^

You can pass a ``json=<function-name>`` parameter to any GET call to have
the results wrapped in a JSON function. This is typically used when browsers
want to embed content received from the API in web pages by getting around
cross domain issues. The response includes the same data output as the regular
API, plus the relevant HTTP Header information.


API Parametrization
-------------------

Since 2.7

Clients should retrieve and process clientconfig.json (see :doc:`clientconfig`)
before making requests to the webservice. If a client can not process the
configuration, it can assume the default configuration given in the
clientconfig.json documentation.


.. _devices:

Devices
-------

Devices are used throughout the API to identify a device / a client
application. A device ID can be any string matching the regular expression
``[\w.-]+``. The client application MUST generate a string to be used as its
device ID, and SHOULD ensure that it is unique within the user account. A good
approach is to combine the application name and the name of the host it is
running on.

If two applications share a device ID, this might cause subscriptions to be
overwritten on the server side. While it is possible to retrieve a list of
devices and their IDs from the server, this SHOULD NOT be used to let a user
select an existing device ID.


Formats
-------
Most of the resources are offered in several different formats

* `OPML <http://www.opml.org/>`_
* JSON
* `JSONP <http://en.wikipedia.org/wiki/JSONP>`_ with an option function name
  that wraps the result (since 2.8)
* plain text with one URL per line
* XML a custom XML format (see `example <http://gpodder.net/toplist.xml>`_,
  since 2.9)


JSON
^^^^

.. code-block:: json

    [
     {
       "website": "http://sixgun.org",
       "description": "The hardest-hitting Linux podcast around",
       "title": "Linux Outlaws",
       "url": "http://feeds.feedburner.com/linuxoutlaws",
       "position_last_week": 1,
       "subscribers_last_week": 1943,
       "subscribers": 1954,
       "mygpo_link": "http://gpodder.net/podcast/11092",
       "logo_url": "http://sixgun.org/files/linuxoutlaws.jpg",
       "scaled_logo_url": "http://gpodder.net/logo/64/fa9fd87a4f9e488096e52839450afe0b120684b4.jpg"
     },
    ]


XML
^^^

.. code-block:: xml

    <podcasts>
     <podcast>
      <title>Linux Outlaws</title>
      <url>http://feeds.feedburner.com/linuxoutlaws</url>
      <website>http://sixgun.org</website>
      <mygpo_link>http://gpodder.net/podcast/11092</mygpo_link>
      <description>The hardest-hitting Linux podcast around</description>
      <subscribers>1954</subscribers>
      <subscribers_last_week>1943</subscribers_last_week>
      <logo_url>http://sixgun.org/files/linuxoutlaws.jpg</logo_url>
      <scaled_logo_url>http://gpodder.net/logo/64/fa9fd87a4f9e488096e52839450afe0b120684b4.jpg</scaled_logo_url>
     </podcast>
    </podcasts>


API Variants
------------

Simple API
^^^^^^^^^^

The Simple API provides a way to upload and download subscription lists in
bulk. This allows developers of podcast-related applications to quickly
integrate support for the web service, as the only

* Synchronization of episode status fields is not supported
* This API uses more bandwith than the advanced API
* The client can be stateless
* The client can be low-powered - subscribe/unsubscribe events are calculated
  on the server-side


Advanced API
^^^^^^^^^^^^

The Advanced API provides more flexibility and enhanced functionality for
applications that want a tighter integration with the web service. A reference
implementation will be provided as part of the gPodder source code (and gPodder
will make use of that reference implementation).

* The client has to persist the synchronization state locally
* Only changes to subscriptions are uploaded and downloaded
* Synchronization of episode status fields is supported in this API
* Only JSON is used as the data format to ease development

