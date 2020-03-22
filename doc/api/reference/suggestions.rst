Suggestions API
===============

Retrieve Suggested Podcasts
---------------------------

..  http:get:: /suggestions/(int:number).(format)
    :synopsis: retrieve suggested podcasts

    * Requires HTTP authentication
    * Since 1.0

    **Example request**:

    .. sourcecode:: http

        GET /suggestions/10.opml

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK

        [
          {
           "website": "http://www.linuxgeekdom.com",
           "mygpo_link": "http://gpodder.net/podcast/64439",
           "description": "Linux Geekdom",
           "subscribers": 0,
           "title": "Linux Geekdom",
           "author": "aj@linuxgeekdom.com (A.J. Stringham)",
           "url": "http://www.linuxgeekdom.com/rssmp3.xml",
           "logo_url": null
         },
         {
           "website": "http://goinglinux.com",
           "mygpo_link": "http://gpodder.net/podcast/11171",
           "description": "Going Linux",
           "subscribers": 571,
           "title": "Going Linux",
           "author": "Larry Bushey",
           "url": "http://goinglinux.com/mp3podcast.xml",
           "logo_url": "http://goinglinux.com/images/GoingLinux80.png"
         }]

    :param number: the maximum number of podcasts to return
    :param format: see :ref:`formats`
    :query jsonp: function name for the JSONP format (since 2.8)

    Download a list of podcasts that the user has not yet subscribed to (by
    checking all server-side subscription lists) and that might be
    interesting to the user based on existing subscriptions (again on all
    server-side subscription lists).

    The TXT format is a simple URL list (one URL per line), and the OPML file
    is a "standard" OPML feed. The JSON format looks as follows:

    The server does not specify the "relevance" for the podcast suggestion, and
    the client application SHOULD filter out any podcasts that are already
    added to the client application but that the server does not know about yet
    (although this is just a suggestion for a good client-side UX).
