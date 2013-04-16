
CouchDB Documents
=================

This page describes the documents that are used in the CouchDB based backend of
the gpodder.net webservice.

User
----

A registered (but probably not yet activated) user and all his devices.

Example Document ::

    {
        username:         "stefan",
        email:            "stefan@gpodder.net",,
        password:         "asdf$asdfasdf$asdfsdfa",
        is_active:        False,
        registration_key: "ad18719239817389ad",

        devices: [
            {
                "_id":   "872348923987492834",
                "user":  "stefan",
                "id":    "n900",
                "type":  "mobile",
                "label": "N900"
            },
            { ... }
        ],

        synchronized: [
            ["872348923987492834", "3498503485093495"],
            ["9384053405", "90548903458"]
        ]
    }



Podcast
-------

If a Podcast does not belong to a group, it is a document on its own.  The
"subscriber" field contains historical subscriber counts. The "tags" field
contains all tags that are fetched in some automated way (ie not entered by a
user).

A Podcast contains recent subscriber data in the "subscribers" property. To
keep the Podcast objects small, subscriber data is periodically moved to the
podcast's PodcastSubscriberData object.


Example Document ::

    {
        _id: "118913287192379173298"
        name: "Cool Podcast",
        feed_url: "http://podcast.com/mp3.xml",
        description: "..."
        subscribers: [{timestamp: "2010-09-01", subscriber_count: 120}, ... },
        related_podcasts: ["34059384598304850", "23480128409230482"],
        tags: {
            feed: [["technology", 50], ["news", 20]],
            delicious: [["technews", 10]]
        },
        publishers: ["stefan"],
        merged_ids: [ ...],
        language: "en",
        episodes: {
            19384038450938450983: { Episode },
            20928340283040234820. { Episode },
        },
        content_types: ["image", "audio"]
    }


PodcastGroup
------------

Represents a group of podcast and contains all podcasts assigned to it.
Once a Podcast is assigned to a group, its Podcast document in deleted
and moved into the PodcastGroup.

Example Document ::

    {
        _id: "9238409283402830480",
        oldid: 10,
        name: "Cool Podcast",
        podcasts: [
            {
                id: "118913287192379173298",
                name: "Cool Podcast",
                group: "9238409283402830480",  # the _id of the group for
                                               # referring to it when the the
                                               # podcast is referred to separately
                group_member_name: "MP3",             # required if Podcast is member of a group
                feed_url: "http://podcast.com/mp3.xml",
                description: "..."
                subscribers: [[2010-09-01, 120], [2010-09-01, 130]],
                related_podcasts: ["34059384598304850", "23480128409230482"],
                tags: ["technology", "news"],
                publishers: ["stefan"],
                episodes: Episode-Dict
            },
            { ... }
        ],
    }



PodcastSubscriberData
---------------------

Contains the older subscriber data for a Podcast. This can be used to retrieve
changes in the number of subscribers of a podcast.

Example Document ::

    {
        podcast: "118913287192379173298",
        subscribers: [
            {timestamp: "2010-09-01", subscriber_count: 120},
            {timestamp: "2010-10-01", subscriber_count: 125},
            {timestamp: "2010-11-01", subscriber_count: 210},
        ],
    }


Episode
-------

An episode, in concept, belongs to a Podcast (not a PodcastGroup) but is a
standalone document. It has optional support for multiple media files (eg Audio
and PDF Show Notes). The fields listeners and recent_listeners are
regularly updated with aggregated data to substitute queries based on time.

Example Document ::

    {
        _id:    "19384038450938450983",
        title: "Cool Episode of Cool Podcast",
        podcast: "118913287192379173298",
        media_urls: ["http://podcast.com/episode1.mp3", "http://podcast.com/episode1.pdf"],
        released: "2010-09-20 12:00",
        tags: ["opensource", "technology"],
        merged_ids: ["908345083045", "29380423849"],
        media_types: ["audio"],
        listeners: [["2010-09-20", 20], ["2010-09-21", 15]],
        recent_listeners:  75,
        language: "en"
    }


PodcastUserState
----------------

Contains everything that a User has done with a Podcast. The podcast is
referenced by the "ref_url" which is the URL that was received via the API. It
can be used in API responses so that the user receives exactly the same URL he
has sent (the Podcast document could contain several URLs).

Example Document ::

    {
        _id: "3893745983453948589345",
        user: "345983045035480345809",
        user_oldid: 4253,
        podcast: "118913287192379173298",
        ref_url: "http://example.com/podcast.xml",
        actions:
            [
                {
                 action:    "subscribed",
                 timestamp: "2010-09-10",
                 device:    "872348923987492834"
                },
                {
                 action:    "unsubscribed",
                 timestamp: "2010-09-15",
                 device:    "872348923987492834"
                }
            ],
        tags: ["technews"]
        settings: { ... }
    }


Suggestions
-----------

Contains the Podcast Suggestions and related meta-data (blacklist,
suggestion-ratings) of a User. This is not places into PodcastUserState
because the user did not yet interact with the Podcast directly.

Example Document ::

    {
        user: "stefan",
        podcasts: [
            "119018023981293801823",
            "192840890284092834093"
        ],
        blacklist: [
            "456045698409586045860",
            "935937498573549739485"
        ],
        ratings: [
            { timestamp: "2010-09-13", rating: -1},
            { timestamp: "2010-09-15", rating:  1}
        ],
    }


EpisodeUserState
----------------

A EpisodeUserState contains everything that a User has done with an Episode.
The episode is referenced by the "ref_url" and "podcast_ref_url" which contain
the URLs for the episode and the podcast, exactly as they have been received
via the API. These values can also be used in API responses to refer to exactly
the same URL as in the request (both Episode and Podcast documents can contain
several URLs).

Example Document ::

    {
        episode: "3893745983453948589345",
        podcast: "118913287192379173298",
        ref_url: "http://podcast.com/episode-1.mp3",
        podcast_ref_url: "http://podcast.com/mp3.xml",
        actions:
            [
                {
                 action:    "download",
                 file:      "http://podcast.com/episode-1.mp3",
                 timestamp: "2010-09-10",
                 device:    "872348923987492834"
                },
                {
                 action:    "play",
                 file:      "http://podcast.com/episode-1.mp3",
                 timestamp: "2010-09-15",
                 device:    "872348923987492834"
                }
            ],
        chapters: [
            {
                from:          "02:10",
                to:            "04:20",
                advertisement: false,
                label:         "interview",
            }
        ],
        settings: { ... }
    }


Advertisement
-------------

Contains an advertisement for a Podcast

Example Document ::

    {
        user:    "stefan",
        podcast: "118913287192379173298",
        start:   "2010-09-01",
        end:     "2010-09-15"
    }


SanitizingRule
--------------

Contains a URL Sanitizing Rule.

Example Document ::

    {
        slug:         "feedburner-feeds2",
        applies_to:   ["podcast", "episode"],
        search:       "http://feeds2\.feedburner\.com",
        replace_by:   "http://feeds.feedburner.com",
        descriptions: "Replace {feeds2 => feeds}.feedburner.com",
        priority:     100,
    }


Category
--------

Represents a category within the Podcast Directory.

Example Document ::

    {
        label:     "Technology",
        spellings: ["technology", "tech"],
        weight:    1200,
        updated:   "2010-09-28T08:38:03Z",
    }
