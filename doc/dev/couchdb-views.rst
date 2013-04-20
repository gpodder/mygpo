
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


Chapters
^^^^^^^^

Doc-Types: EpisodeUserState

**Views**

* chapters/by_episode


Clients
^^^^^^^

Doc-Types: User

**Views**

* clients/by_ua_string


Episode Actions
^^^^^^^^^^^^^^^

Doc-Types: EpisodeUserState

**Views**

* episode_actions/by_device
* episode_actions/by_podcast_device
* episode_actions/by_podcast
* episode_actions/by_user


Episode States
^^^^^^^^^^^^^^

Doc-Types: EpisodeUserState

**Views**

* episode_states/by_podcast_episode
* episode_states/by_ref_urls
* episode_states/by_user_episode
* episode_states/by_user_podcast


Episode Statistics
^^^^^^^^^^^^^^^^^^

Doc-Types: Episode

**Views**

* episode_stats/filetypes


Episodes
^^^^^^^^

Doc-Types: Episode

**Views**

* episodes/by_id
* episodes/by_oldid
* episodes/by_podcast
* episodes/by_podcast_url
* episodes/by_slug
* episodes/need_update


Favorites
^^^^^^^^^

Doc-Types: EpisodeUserState

**Views**

* episodes/favorites_by_user


Heatmap
^^^^^^^

Doc-Types: EpisodeUserState

**Views**

* heatmap/by_episode


History
^^^^^^^

Doc-Types: EpisodeUserState, PodcastUserState

**Views**

* history/by_device
* history/by_user


Listeners
^^^^^^^^^

Doc-Types: EpisodeUserState

**Views**

* listeners/by_episode
* listeners/by_podcast_episode
* listeners/by_podcast
* listeners/by_user
* listeners/by_user_podcast
* listeners/times_played_by_user


Podcast Lists
^^^^^^^^^^^^^

Doc-Types: PodcastList

**Views**

* podcastlists/by_rating
* podcastlists/by_user_slug
* podcastlists/random


Podcast States
^^^^^^^^^^^^^^

Doc-Types: PodcastUserState

**Views**

* podcast_states/by_device
* podcast_states/by_podcast
* podcast_states/by_user


Podcasts
^^^^^^^^

Doc-Types: Podcast, PodcastGroup, PodcastSubscriberData

**Views**

* podcasts/by_id
* podcasts/by_language
* podcasts/by_last_update
* podcasts/by_oldid
* podcasts/by_slug
* podcasts/by_tag
* podcasts/by_url
* podcasts/flattr
* podcasts/groups_by_oldid
* podcasts/podcasts_groups
* podcasts/random
* podcasts/subscriber_data


Sanitizing Rules
^^^^^^^^^^^^^^^^

Doc-Types: SanitizingRule

**Views**

* sanitizing_rules/by_slug
* sanitizing_rules/by_target


Slugs
^^^^^

Doc-Types: Podcast, PodcastGroup, Episode

**Views**

* slugs/missing


Subscribers
^^^^^^^^^^^

Doc-Types: PodcastUserState

**Views**

* subscribers/by_podcast


Subscriptions
^^^^^^^^^^^^^

Doc-Types: PodcastUserState

**Views**

* subscriptions/by_device
* subscriptions/by_podcast
* subscriptions/by_user


Suggestions
^^^^^^^^^^^

Doc-Types: Suggestions

**Views**

* suggestions/by_user


Tags
^^^^

Doc-Types: Podcast, PodcastGroup

**Views**

* tags/by_podcast
* tags/by_user


Toplists
^^^^^^^^

Doc-Types: Episode, Podcast, PodcastGroup

**Views**

* toplist/episodes
* toplist/podcasts


Trending
^^^^^^^^

Doc-Types: Podcast, PodcastGroup

**Views**

* trending/podcasts


Users
^^^^^

Doc-Types: User

**Views**

* users/by_google_email
* users/deleted


User-Tags
^^^^^^^^^

Doc-Types: PodcastUserState

* usertags/by_podcast
* usertags/podcasts



Categories
----------

This group of views is available on the categories database, called
``mygpo_categories`` by default.


Categories
^^^^^^^^^^

Doc-Types: Category

**Views**

* categories/by_tags
* categories/by_update
