Directory API
=============


.. _api-top-tags:

Retrieve Top Tags
-----------------

..  http:get:: /api/2/tags/(int:count).json
    :synopsis: Returns a list of the count most used tags.

    * Does not require authentication
    * Since 2.2

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK

        [
          {
           "title": "Technology",
           "tag": "technology",
           "usage": 530
          },
          {
           "title": "Society & Culture",
           "tag": "society-culture",
           "usage": 420
          },
          {
           "title": "Arts",
           "tag": "arts",
           "usage": 400
          },
          {
           "title": "News & Politics",
           "tag": "News & Politics",
           "usage": 320
          }
        ]

    :param count: number of tags to return



.. _api-podcasts-tag:

Retrieve Podcasts for Tag
-------------------------

..  http:get:: /api/2/tag/(tag)/(int:count).json
    :synopsis: Returns the most-subscribed podcasts that are tagged with tag.

    * Does not require authentication
    * Since 2.2

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK

        [
         {"url": "http://leo.am/podcasts/floss",
          "title": "FLOSS Weekly",
          "author": "Leo Laporte",
          "description": "Each Thursday we talk about Free Libre and Open Source Software with the people who are writing it. Part of the TWiT Netcast Network.",
          "subscribers": 1138,
          "logo_url: "http://leoville.tv/podcasts/coverart/floss144audio.jpg",
          "website": "http://twit.tv/",
          "mygpo_link": "http://gpodder.net/podcast/12925"},

         {"url": "http://leo.am/podcasts/twit",
          "title": "this WEEK in TECH - MP3 Edition",
          "author": "Leo Laporte",
          "description": "Your first podcast of the week is the last word in tech. [...]",
          "subscribers": 895,
          "logo_url": "http://leoville.tv/podcasts/coverart/twit144audio.jpg",
          "website": "http://thisweekintech.com/",
          "mygpo_link": "http://thisweekintech.com/"}
        ]

    :param tag: URL-encoded tag
    :param count: maximum number of podcasts to return



.. _api-podcast-data:

Retrieve Podcast Data
---------------------

.. http:get:: /api/2/data/podcast.json

    Returns information for the podcast with the given URL or 404 if there is
    no podcast with this URL.

    * No authentication required
    * Since 2.2

    .. sourcecode:: http

        HTTP/1.1 200 OK

        {
         "website": "http://coverville.com",
         "mygpo_link": "http://www.gpodder.net/podcast/16124",
         "description": "The best cover songs, delivered to your ears two to three times a week!",
         "subscribers": 19,
         "title": "Coverville",
         "author": "Brian Ibbott",
         "url": "http://feeds.feedburner.com/coverville",
         "subscribers_last_week": 19,
         "logo_url": "http://www.coverville.com/art/coverville_iTunes300.jpg"
        }

    ::query url: the feed URL of the podcast


.. _api-episode-data:

Retrieve Episode Data
---------------------

.. http:get:: /api/2/data/episode.json

    Returns information for the episode with the given {url} that
    belongs to the podcast with the {podcast}

    * Does not require authentication
    * Since 2.2 (added released in 2.6)

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK

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

    ::query podcast: feed URL of the podcast to which the episode belongs
    ::query url: media URL of the episode


Podcast Toplist
---------------

..  http:get:: /toplist/(int:number).(format)
    :synopsis: Get list of most popular podcasts

    * Does not require authentication (public content)
    * Since 1.0

    **Example request**:

    .. sourcecode:: http

        GET /toplist/50.json

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK

        [
         {
           "website": "http://linuxoutlaws.com/podcast",
           "description": "Open source talk with a serious attitude",
           "title": "Linux Outlaws",
           "author": "Sixgun Productions",
           "url": "http://feeds.feedburner.com/linuxoutlaws",
           "position_last_week": 0,
           "subscribers_last_week": 1736,
           "subscribers": 1736,
           "mygpo_link": "http://www.gpodder.net/podcast/11092",
           "logo_url": "http://linuxoutlaws.com/files/albumart-itunes.jpg"
         },
         {
           "website": "http://syndication.mediafly.com/redirect/show/d581e9b773784df7a56f37e1138c037c",
           "description": "We're not talking dentistry here; FLOSS all about Free Libre Open Source Software. Join hosts Randal Schwartz and Leo Laporte every Saturday as they talk with the most interesting and important people in the Open Source and Free Software community.",
           "title": "FLOSS Weekly Video (large)",
           "author": "Leo Laporte",
           "url": "http://feeds.twit.tv/floss_video_large",
           "position_last_week": 0,
           "subscribers_last_week": 50,
           "subscribers": 50,
           "mygpo_link": "http://www.gpodder.net/podcast/31991",
           "logo_url": "http://static.mediafly.com/publisher/images/06cecab60c784f9d9866f5dcb73227c3/icon-150x150.png"
         }]

    :query jsonp: a functionname on which the response is wrapped (only valid
                  for format ``jsonp``; since 2.8)
    :query scale_logo: returns logo URLs to scaled images, see below.
    :param number: maximum number of podcasts to return
    :param format: see :ref:`formats`


    The number field might be any value in the range 1..100 (inclusive both
    boundaries).

    For the JSON and XML formats, an optional paramter scale_logo={size} can be
    passed, which provides a link to a scaled logo (scaled_logo_url) for each
    podcast. size has to be a positive number up to 256 and defaults to 64.

    The OPML and TXT formats do not add any information about the (absolute and
    relative) popularity for each podcast, only the ordering can be
    considered. The JSON format includes a more detailed list, usable for
    clients that want to display a detailed toplist or post-process the
    toplist:

    All shown keys must be provided by the server. The description field may be
    set to the empty string in case a description is not available. The title
    field may be set to the URL in case a title is not available. The
    subscribers_last_week field may be set to zero if no data is available. The
    client can use the subscribers_last_week counts to re-sort the list and get
    a ranking for the last week. With this information, a relative "position
    movement" can also be calculated if the developer of the client decides to
    do so.


Podcast Search
--------------

.. http:get:: /search.(format)

    Carries out a service-wide search for podcasts that match the given query.
    Returns a list of podcasts. See :ref:`formats` for details on the response
    formats.

    * Does not require authentication (public content)
    * Since 2.0

    :query q: search query
    :query jsonp: used to wrap the JSON results in a function call (JSONP); the
                   value of this parameter is the name of the function; since
                   2.8
    :query scale_logo: when set, the results (only JSON and XML formats)
                       include links to the podcast logos that are scaled to
                       the requested size. The links are provided in the
                       scaled_logo_url field; since 2.9
    :param format: see :ref:`formats`
