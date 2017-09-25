Favorites API
=============


.. _api-favorite-episodes:

Get Favorite Episodes
---------------------

..  http:get:: /api/2/favorites/(username).json
    :synopsis: return the user's favorite episodes

    * Requires Authentication
    * Since 2.4 (added released in 2.6)

    The response is a list of all favorite episodes, as they can be seen on http://gpodder.net/favorites/

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK

        [
           {
             "title": "TWiT 245: No Hitler For You",
             "url": "http://www.podtrac.com/pts/redirect.mp3/aolradio.podcast.aol.com/twit/twit0245.mp3",
             "podcast_title": "this WEEK in TECH - MP3 Edition",
             "podcast_url": "http://leo.am/podcasts/twit",
             "description": "[...]",
             "website": "http://www.podtrac.com/pts/redirect.mp3/aolradio.podcast.aol.com/twit/twit0245.mp3",
             "released": "2010-12-25T00:30:00",
             "mygpo_link": "http://gpodder.net/episode/1046492"
            }
        ]

    :param username: username for which the favorites should be returned
