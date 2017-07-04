Episode Actions API
===================

The episode actions API is used to synchronize episode-related events between
individual devices. Clients can send and store events on the webservice which
makes it available to other clients. The following types of actions are
currently accepted by the API: download, play, delete, new. Additional types
can be requested on the Mailing List.

Example use cases

* Clients can send ``download`` and ``delete`` events so that other clients
  know where a file has already been downloaded.
* Clients can send ``play`` events with ``position`` information so that other
  clients know where to start playback.
* Clients can send ``new`` states to reset previous events. This state needs
  to be interpreted by receiving clients and does not delete any information
  on the webservice.


.. _episode-action-types:

Episode Action Types
--------------------

* download
* delete
* play
* new
* flattr


Upload Episode Actions
----------------------

..  http:post:: /api/2/episodes/(username).json
    :synopsis: Upload new episode actions

    * Requires HTTP authentication
    * Since 2.0

    Upload changed episode actions. As actions are saved on a per-user basis
    (not per-device), the API endpoint is the same for every device. For
    logging purposes, the client can send the device ID to the server, so it
    appears in the episode action log on the website.

    **Example request**:

    .. sourcecode:: http

        POST /api/2/episodes/some-user.json

        [
          {
           "podcast": "http://example.com/feed.rss",
           "episode": "http://example.com/files/s01e20.mp3",
           "device": "gpodder_abcdef123",
           "action": "download",
           "timestamp": "2009-12-12T09:00:00"
          },
          {
           "podcast": "http://example.org/podcast.php",
           "episode": "http://ftp.example.org/foo.ogg",
           "action": "play",
           "started": 15,
           "position": 120,
           "total":  500
          }
        ]

    :<json podcast: The feed URL to the podcast feed the episode belongs to (required)
    :<json episode: The media URL of the episode (required)
    :<json device: The device ID on which the action has taken place (see :ref:`devices`)
    :<json action: One of: download, play, delete, new (required)
    :<json timestamp: A UTC timestamp when the action took place, in ISO 8601 format
    :<json started: Only valid for "play". the position (in seconds) at which the client started playback. Requires position and total to be set.
    :<json position: Only valid for "play". the position (in seconds) at which the client stopped playback
    :<json total: Only valid for "play". the total length of the file in seconds. Requires position and started to be set.

    **Example response**:

    The return value is a JSON dictionary containing the timestamp and a list
    of URLs that have been rewritten (sanitized, see bug:747 and bug:862) as a
    list of tuples with the key "update_urls". The client SHOULD parse this
    list and update the local subscription and episode list accordingly (the
    server only sanitizes the URL, so the semantic "content" should
    stay the same and therefore the client can simply update the URL
    value locally and use it for future updates. An example result with
    update_urls:

    .. sourcecode:: http

        HTTP/1.1 200 OK

        {
            "timestamp": 1337,
            "update_urls": [
                ["http://feeds2.feedburner.com/LinuxOutlaws?format=xml",
                 "http://feeds.feedburner.com/LinuxOutlaws"],
                ["http://example.org/episode.mp3 ",
                 "http://example.org/episode.mp3"]
            ]
        }

    URLs that are not allowed (currently all URLs that contain non-ASCII
    characters or don't start with either http or https) are rewritten to
    the empty string and are ignored by the Webservice.


Get Episode Actions
-------------------

..  http:get:: /api/2/episodes/(username).json
    :synopsis: retrieve new episode actions

    * Requires HTTP authentication
    * Since 2.0


    Timestamps: The result is a list of all episode actions that were uploaded
    since the timestamp given in the since parameter (regardless of the action
    timestamp itself). The timestamp SHOULD be the value returned by
    the previous episode retrieve request. If no since value is given, ALL
    episode actions for the given user are returned. Please note that this
    could be a potentially long list of episode actions, so clients SHOULD
    provide a since value whenever possible (e.g. when uploads have been taken
    place before).

    **Example response**:

    The format of the action list is the same as with the action upload
    request, but the format is a bit different so that the server can send the
    new timestamp (that the client SHOULD save and use for subsequent
    requests):

    .. sourcecode:: http

        HTTP/1.1 200 OK

        {
            "actions": [],
            "timestamp": 12345
        }

    Client implementation notes: A client can make use of the device variant of
    this request when it is assigned a single device id. When adding a podcast
    to the client (without synching the subscription list straight away), the
    variant with the podcast URL can be used. The first variant (no parameters
    at all) can be used as a kind of "burst" download of all episode
    actions, but should be used as little as possible (e.g. after a re-install,
    although even then, the device-id parameter could be more useful).

    :query string podcast: The URL of a Podcast feed; if set, only actions for episodes of the given podcast are returned
    :query string device: A Device ID; if set, only actions for the given device are returned
    :query int since: Only episode actions since the given timestamp are returned
    :query bool aggregated: If true, only the latest actions is returned for each episode (added in 2.1)
