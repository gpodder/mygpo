
CouchDB Views
=============

This page describes the views that will be used in the CouchDB based backend of
the gpodder.net webservice.

The views are separated into groups, based on the databases they are indexed
on.

General
-------

This group of views is available on the general database, called ``mygpo`` by
default.


Clients
^^^^^^^

Doc-Types: User

**Views**

* `clients/by_ua_string <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/clients/views/by_ua_string>`_


Users
^^^^^

Doc-Types: User

**Views**

* `users/by_google_email <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/users/views/by_google_email>`_
* `users/deleted <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/users/views/deleted>`_


Userdata
--------

This group of views is available in the *userdata* database, called
``mygpo_userdata`` by default.

Chapters
^^^^^^^^

Doc-Types: EpisodeUserState

**Views**

* `chapters/by_episode <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/chapters/views/by_episode>`_


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


Podcast States
^^^^^^^^^^^^^^

Doc-Types: PodcastUserState

**Views**

* `podcast_states/by_device <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/podcast_states/views/by_device>`_
* `podcast_states/by_podcast <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/podcast_states/views/by_podcast>`_
* `podcast_states/by_user <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/podcast_states/views/by_user>`_


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


User-Tags
^^^^^^^^^

Doc-Types: PodcastUserState

**Views**

* `usertags/by_podcast <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/usertags/views/by_podcast>`_
* `usertags/by_user <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/usertags/views/by_user>`_
* `usertags/podcasts <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/usertags/views/podcasts>`_





Categories
----------

This group of views is available on the categories database, called
``mygpo_categories`` by default.


Categories
^^^^^^^^^^

Doc-Types: Category

**Views**

* `categories/by_tags <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/categories/views/by_tags>`_
* `categories/by_update <https://github.com/gpodder/mygpo/tree/master/couchdb/general/_design/categories/views/by_update>`_
