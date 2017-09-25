Subscriptions API
=================

Get Subscriptions of Device
---------------------------

..  http:get:: /subscriptions/(username)/(deviceid).(format)
    :synopsis: Get a list of subscribed podcasts for the given user.

    * Requires HTTP authentication
    * Since 1.0

    **Example request**:

    .. sourcecode:: http

        GET /subscriptions/bob/asdf.opml

    :param username: username for which subscriptions should be returned
    :param deviceid: see :ref:`devices`
    :param format: see :ref:`formats`
    :query jsonp: function name for the JSONP format (since 2.8)

    :status 200: the subscriptions are returned in the requested format
    :status 401: Invalid user
    :status 404: Invalid device ID
    :status 400: Invalid format


.. _api-subscriptions-all:

Get All Subscriptions
---------------------

..  http:get:: /subscriptions/(username).(format)
    :synopsis: Get a list of all subscribed podcasts for the given user.

    * Requires HTTP authentication
    * Since 2.11

    **Example request**:

    .. sourcecode:: http

        GET /subscriptions/bob.opml

    This can be used to present the user a list of podcasts when the
    application starts for the first time.

    :param username: username for which subscriptions should be returned
    :param deviceid: see :ref:`devices`
    :param format: see :ref:`formats`
    :query jsonp: function name for the JSONP format (since 2.8)

    :status 200: the subscriptions are returned in the requested format
    :status 401: Invalid user
    :status 400: Invalid format


Upload Subscriptions of Device
------------------------------

..  http:put:: /subscriptions/(username)/(deviceid).(format)
    :synopsis: Upload subscriptions

    * Requires HTTP authentication
    * Since 1.0

    Upload the current subscription list of the given user to the server. The
    data should be provided either in OPML, JSON or plaintext (one URL per
    line) format, and should be uploaded just like a normal PUT request
    (i.e. in the body of the request).

    For successful updates, the implementation always returns the status code
    200 and the empty string (i.e. an empty HTTP body) as a result, any other
    string should be interpreted by the client as an (undefined) error.

    **Example request**:

    .. sourcecode:: http

        PUT /subscriptions/john/e9c4ea4ae004efac40.txt

    :param username: username for which subscriptions should be uploaded
    :param deviceid: see :ref:`devices`
    :param format: see :ref:`formats`

    :status 200: the subscriptions have been updated
    :status 401: Invalid user
    :status 400: Invalid format

    In case the device does not exist for the given user, it is automatically
    created. If clients want to determine if a device exists, you have to to a
    GET request on the same URL first and check for a the 404 status code (see
    above).


.. _api-subscriptions-change-add:

Upload Subscription Changes
---------------------------

..  http:post:: /api/2/subscriptions/(username)/(deviceid).json
    :synopsis: Update the subscription list for a given device.

    * Requires HTTP authentication
    * Since 2.0

    Only deltas are supported here. Timestamps are not supported, and are
    issued by the server.

    **Example request**:

    .. sourcecode:: http

        {
            "add": ["http://example.com/feed.rss", "http://example.org/podcast.php"],
            "remove": ["http://example.net/foo.xml"]
        }

    :param username: username for which subscriptions should be returned
    :param deviceid: see :ref:`devices`
    :status 400: the same feed has been added and removed in the same request
    :status 200: the subscriptions have been updated

    In positive responses the server returns a timestamp/ID that can be used
    for requesting changes since this upload in a subsequent API call. In
    addition, the server sends a list of URLs that have been rewritten
    (sanitized, see bug:747) as a list of tuples with the key "update_urls".
    The client SHOULD parse this list and update the local subscription list
    accordingly (the server only sanitizes the URL, so the semantic "content"
    should stay the same and therefore the client can simply update the
    URL value locally and use it for future updates.

    **Example response**:

    .. sourcecode:: http

        {
          "timestamp": 1337,
          "update_urls":
           [
            [
             "http://feeds2.feedburner.com/LinuxOutlaws?format=xml",
             "http://feeds.feedburner.com/LinuxOutlaws"
            ],
            [
             "http://example.org/podcast.rss ",
             "http://example.org/podcast.rss"
            ]
           ]
        }

    URLs that are not allowed (currently all URLs that don't start with either
    http or https) are rewritten to the empty string and are ignored by
    the Webservice.


.. _api-subscriptions-change-get:

Get Subscription Changes
------------------------

..  http:get:: /api/2/subscriptions/(username)/(deviceid).json
    :synopsis: retrieve subscription changes

    * Requires HTTP authentication
    * Since 2.0

    This API call retrieves the subscription changes since the timestamp
    provided in the since parameter. Its value SHOULD be timestamp value from
    the previous call to this API endpoint. If there has been no previous call,
    the cliend SHOULD use 0.

    The response format is the same as the upload format: A dictionary with two
    keys "add" and "remove" where the value for each key is a list of URLs that
    should be added or removed. The timestamp SHOULD be stored by the client in
    order to provide it in the since parameter in the next request.

    **Example response**:

    In case nothing has changed, the server returns something like the
    following JSON content.

    .. sourcecode:: http

        {
           "add": [],
           "remove": [],
           "timestamp": 12347
        }

    :param username: username for which subscriptions should be returned
    :param deviceid: see :ref:`devices`
    :query since: the ``timestamp`` value of the last response
