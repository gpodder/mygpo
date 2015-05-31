Client Parametrization
======================

The client configuration file is located at
http://gpodder.net/clientconfig.json and contains information that clients
should retrieve before making requests to the APIs.

If a client cannot retrieve and process this file (either temporarily or
permanently), it can assume the default values provided below. However,
the URLs in the file might reflect changed URLs and/or mirror servers. If a
client decides to permanently ignore this file, it might hit an outdated URL
or an overloaded server.


Commented Example
-----------------

.. code-block:: json

    {
        "mygpo":  {
            "baseurl": "http://gpodder.net/"
        }

        "mygpo-feedservice": {
            "baseurl": "http://mygpo-feedservice.appspot.com/"
        }

        "update_timeout": 604800,
    }

* ``mygpo/baseurl``: URL to which the gpodder.net API Endpoints should be appended
* ``mygpo-feedservice/baseurl``: Base URL of the gpodder.net feed service
* ``update_timeout``: Time in seconds for which the values in this file can be considered valid.
