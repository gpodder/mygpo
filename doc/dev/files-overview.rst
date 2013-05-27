File Overview
=============

The ``mygpo`` project consists of the following files ::

  mygpo/
    __init__.py
    settings.py                                                # default settings
    settings_prod.py                                           # "productive" settings which overwrite those in settings.py
    cache.py                                                   # utils around Django's cache
    manage.py                                                  # https://docs.djangoproject.com/en/dev/ref/django-admin/
    constants.py                                               # defines some global constants
    flattr.py                                                  # Flattr support (https://flattr.com/)
    utils.py                                                   # utilities
    cel.py                                                     # Celery integration (http://celeryproject.org/)
    urls.py                                                    # Django URL dispatcher (https://docs.djangoproject.com/en/dev/topics/http/urls/)
    shell.py                                                   # import * for commonly used methods when working in the Django shell
    test.py                                                    # custom Django test suite runner
    decorators.py                                              # globally used decorators
    print-couchdb.py                                           # script to print the main CouchDB database

    admin/                                                     # functionality to be used by site-admins
      auth.py                                                  # authentication of admins
      group.py                                                 # groups / matches episodes (eg for merging)
      clients.py                                               # client statistics
      views.py                                                 # Django views for the admin area (https://docs.djangoproject.com/en/dev/topics/http/views/)
      urls.py                                                  # Django URL dispatcher for the admin area
      tasks.py                                                 # Celery tasks

    maintenance/
      merge.py                                                 # Merging of podcasts and related objects
      management/changescmd.py                                 # base class for commands that use the CouchDB changes feed (https://couchdb.readthedocs.org/en/latest/changes.html)
      management/podcastcmd.py                                 # base class for commands that operate on (multiple) podcasts
      management/commands/celery.py                            # Celery worker
      management/commands/assign-podcast-slugs.py              # assigns slugs to podcasts (one-time command, now unused)
      management/commands/cleanup-unused-users.py              # removes users that have been marked as deleted
      management/commands/assign-episode-slugs.py              # assigns slugs to episodes (one-time command, now unused)
      management/commands/listening-stats.py                   # stats about the intervald between publishing and playing episodes
      management/commands/merge-episode-states.py              # merges duplicates of episodes states
      management/commands/move-subscriber-data.py              # moves subscriber data from podcasts into separate objects
      management/commands/import-episode-actions.py            # imports episode actions from files

    data/                                                      # stuff related to podcast and episode data
      youtube.py                                               # utils for accessing YouTube data
      delicious.py                                             # utils for accessing delicious.com data
      flickr.py                                                # utils for accessing Flickr data
      podcast.py                                               # podcast-related utils
      mimetype.py                                              # utils for handling mime types
      signals.py                                               # Django Signals for podcast-related events (https://docs.djangoproject.com/en/dev/topics/signals/)
      tasks.py                                                 # podcast-related Celery tasks
      feeddownloader.py                                        # fetching, parsing and updating podcasts based on their feeds
      management/commands/feed-downloader.py                   # command-wrapper around feeddownloader.py
      management/commands/update-related-podcasts.py           # calculates and sets related podcasts for existing podcasts
      management/commands/tag-downloader.py                    # fetches and updates tags for existing podcasts
      management//commands/group-podcasts.py                   # group two related podcasts

    publisher/
      __init__.py
      auth.py
      tests.py
      forms.py
      utils.py
      views.py
      urls.py
      management/__init__.py
      management/commands/make-publisher.py
      management/commands/__init__.py
      templatetags/__init__.py
      templatetags/pcharts.py

    users/
      __init__.py
      tests.py
      sync.py
      models.py
      settings.py
      ratings.py
      signals.py
      tasks.py
      subscriptions.py
      management/__init__.py
      management/commands/__init__.py
      management/commands/assign-upload-timestamps.py

    api/
      __init__.py
      tests.py
      backend.py
      constants.py
      opml.py
      legacy.py
      models.py
      exceptions.py
      views.py
      urls.py
      basic_auth.py
      httpresponse.py
      simple.py
      tasks.py
      advanced/auth.py
      advanced/sync.py
      advanced/lists.py
      advanced/settings.py
      advanced/__init__.py
      advanced/episode.py
      advanced/directory.py
      management/commands/__init__.py
      management/__init__.py

    directory/
      __init__.py
      tests.py
      models.py
      views.py
      urls.py
      search.py
      toplist.py
      tags.py
      tasks.py
      management/__init__.py
      management/commands/__init__.py
      management/commands/category-merge-spellings.py
      management/commands/update-episode-toplist.py
      management/commands/set-example-podcasts.py
      management/commands/update-toplist.py

    pubsub
      models.py
      views.py
      urls.py
      __init__.py
      signals.py

    web/
      __init__.py
      auth.py
      tests.py
      forms.py
      google.py
      utils.py
      logo.py
      urls.py
      heatmap.py
      views/__init__.py
      views/podcast.py
      views/settings.py
      views/subscriptions.py
      views/device.py
      views/users.py
      views/episode.py
      views/security.py
      templatetags/__init__.py
      templatetags/devices.py
      templatetags/facebook.py
      templatetags/youtube.py
      templatetags/google.py
      templatetags/utils.py
      templatetags/time.py
      templatetags/flickr.py
      templatetags/math.py
      templatetags/mygpoutil.py
      templatetags/menu.py
      templatetags/charts.py
      templatetags/podcasts.py
      templatetags/episodes.py
      templatetags/googleanalytics.py
      management/__init__.py
      management/commands/__init__.py

    userfeeds/
      __init__.py
      auth.py
      tests.py
      feeds.py
      views.py
      urls.py

    core/
      __init__.py
      tests.py
      oldid.py
      json.py
      models.py
      proxy.py
      signals.py
      podcasts.py
      tasks.py
      graphite.py
      slugs.py
      management/__init__.py
      management/commands/__init__.py

    share/
      __init__.py
      userpage.py
      models.py
      views.py
      urls.py
      templatetags/__init__.py
      templatetags/gravatar.py

    db/
      __init__.py

    db/couchdb/
      __init__.py
      common.py
      episode_state.py
      utils.py
      user.py
      models.py
      podcast_state.py
      podcast.py
      podcastlist.py
      episode.py
      directory.py
      pubsub.py
      management/__init__.py
      management/commands/__init__.py
      management/commands/touch-couchdb-views.py
      management/commands/compact-couchdb.py
      management/commands/dump-sample.py
      management/commands/sync-design-docs.py
      management/commands/count-view-usage.py
