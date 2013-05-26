
CouchDB Views
=============

This page describes the views that will be used in the CouchDB based backend of
the gpodder.net webservice.

General
-------

The following views and design documents relate to the "main" database.

Categories
^^^^^^^^^^

Doc-Types: Category

**Views**

* `categories/by_tags <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/categories/views/by_tags>`_
* `categories/by_update <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/categories/views/by_update>`_


Chapters
^^^^^^^^

Doc-Types: EpisodeUserState

**Views**

* `chapters/by_episode <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/chapters/views/by_episode>`_


Clients
^^^^^^^

Doc-Types: User

**Views**

* `clients/by_ua_string <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/clients/views/by_ua_string>`_


Episode Actions
^^^^^^^^^^^^^^^

Doc-Types: EpisodeUserState

**Views**

* `episode_actions/by_device <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/episode_actions/views/by_device>`_
* `episode_actions/by_podcast_device <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/episode_actions/views/by_podcast_device>`_
* `episode_actions/by_podcast <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/episode_actions/views/by_podcast>`_
* `episode_actions/by_user <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/episode_actions/views/by_user>`_


Episode States
^^^^^^^^^^^^^^

Doc-Types: EpisodeUserState

**Views**

* `episode_states/by_podcast_episode <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/episode_states/views/by_podcast_episode>`_
* `episode_states/by_ref_urls <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/episode_states/views/by_ref_urls>`_
* `episode_states/by_user_episode <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/episode_states/views/by_user_episode>`_
* `episode_states/by_user_podcast <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/episode_states/views/by_user_podcast>`_


Episode Statistics
^^^^^^^^^^^^^^^^^^

Doc-Types: Episode

**Views**

* `episode_stats/filetypes <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/episode_stats/views/filetypes>`_


Episodes
^^^^^^^^

Doc-Types: Episode

**Views**

* `episodes/by_id <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/episodes/views/by_id>`_
* `episodes/by_oldid <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/episodes/views/by_oldid>`_
* `episodes/by_podcast <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/episodes/views/by_podcast>`_
* `episodes/by_podcast_url <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/episodes/views/by_podcast_url>`_
* `episodes/by_slug <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/episodes/views/by_slug>`_
* `episodes/need_update <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/episodes/views/need_update>`_


Favorites
^^^^^^^^^

Doc-Types: EpisodeUserState

**Views**

* `episodes/favorites_by_user <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/favorites/views/episodes_by_user>`_


Heatmap
^^^^^^^

Doc-Types: EpisodeUserState

**Views**

* `heatmap/by_episode <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/heatmap/views/by_episode>`_


History
^^^^^^^

Doc-Types: EpisodeUserState, PodcastUserState

**Views**

* `history/by_device <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/history/views/by_device>`_
* `history/by_user <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/history/views/by_user>`_


Listeners
^^^^^^^^^

Doc-Types: EpisodeUserState

**Views**

* `listeners/by_episode <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/listeners/views/by_episode>`_
* `listeners/by_podcast_episode <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/listeners/views/by_podcast_episode>`_
* `listeners/by_podcast <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/listeners/views/by_podcast>`_
* `listeners/by_user <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/listeners/views/by_user>`_
* `listeners/by_user_podcast <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/listeners/views/by_user_podcast>`_
* `listeners/times_played_by_user <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/listeners/views/times_played_by_user>`_


Podcast Lists
^^^^^^^^^^^^^

Doc-Types: PodcastList

**Views**

* `podcastlists/by_rating <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/podcastlists/views/by_rating>`_
* `podcastlists/by_user_slug <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/podcastlists/views/by_user_slug>`_
* `podcastlists/random <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/podcastlists/views/random>`_


Podcast States
^^^^^^^^^^^^^^

Doc-Types: PodcastUserState

**Views**

* `podcast_states/by_device <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/podcast_states/views/by_device>`_
* `podcast_states/by_podcast <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/podcast_states/views/by_podcast>`_
* `podcast_states/by_user <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/podcast_states/views/by_user>`_


Podcasts
^^^^^^^^

Doc-Types: Podcast, PodcastGroup, PodcastSubscriberData

**Views**

* `podcasts/by_id <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/podcasts/views/by_id>`_
* `podcasts/by_language <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/podcasts/views/by_language>`_
* `podcasts/by_last_update <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/podcasts/views/by_last_update>`_
* `podcasts/by_oldid <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/podcasts/views/by_oldid>`_
* `podcasts/by_slug <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/podcasts/views/by_slug>`_
* `podcasts/by_tag <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/podcasts/views/by_tag>`_
* `podcasts/by_url <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/podcasts/views/by_url>`_
* `podcasts/flattr <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/podcasts/views/flattr>`_
* `podcasts/groups_by_oldid <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/podcasts/views/groups_by_oldid>`_
* `podcasts/podcasts_groups <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/podcasts/views/podcasts_groups>`_
* `podcasts/random <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/podcasts/views/random>`_
* `podcasts/subscriber_data <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/podcasts/views/subscriber_data>`_


Sanitizing Rules
^^^^^^^^^^^^^^^^

Doc-Types: SanitizingRule

**Views**

* `sanitizing_rules/by_slug <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/sanitizing_rules/views/by_slug>`_
* `sanitizing_rules/by_target <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/sanitizing_rules/views/by_target>`_


Slugs
^^^^^

Doc-Types: Podcast, PodcastGroup, Episode

**Views**

* `slugs/missing <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/slugs/views/missing>`_


Subscribers
^^^^^^^^^^^

Doc-Types: PodcastUserState

**Views**

* `subscribers/by_podcast <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/subscribers/views/by_podcast>`_


Subscriptions
^^^^^^^^^^^^^

Doc-Types: PodcastUserState

**Views**

* `subscriptions/by_device <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/subscriptions/views/by_device>`_
* `subscriptions/by_podcast <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/subscriptions/views/by_podcast>`_
* `subscriptions/by_user <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/subscriptions/views/by_user>`_


Suggestions
^^^^^^^^^^^

Doc-Types: Suggestions

**Views**

* `suggestions/by_user <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/suggestions/views/by_user>`_


Tags
^^^^

Doc-Types: Podcast, PodcastGroup

**Views**

* `tags/by_podcast <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/tags/views/by_podcast>`_
* `tags/by_user <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/tags/views/by_user>`_


Toplists
^^^^^^^^

Doc-Types: Episode, Podcast, PodcastGroup

**Views**

* `toplist/episodes <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/toplist/views/episodes>`_
* `toplist/podcasts <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/toplist/views/podcasts>`_


Trending
^^^^^^^^

Doc-Types: Podcast, PodcastGroup

**Views**

* `trending/podcasts <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/trending/views/podcasts>`_


Users
^^^^^

Doc-Types: User

**Views**

* `users/by_google_email <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/users/views/by_google_email>`_
* `users/deleted <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/users/views/deleted>`_


User-Tags
^^^^^^^^^

Doc-Types: PodcastUserState

* `usertags/by_podcast <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/usertags/views/by_podcast>`_
* `usertags/podcasts <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/usertags/views/podcasts>`_



Pubsub
------

The following views and design documents relate to the "pubsub" database.

Subscriptions
^^^^^^^^^^^^^

Doc-Types: Subscription

* `subscriptions/by_topic <https://github.com/gpodder/mygpo/tree/master/couchdb/pubsub/_design/subscriptions/views/by_topic>`_
