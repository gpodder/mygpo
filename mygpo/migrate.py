from couchdbkit import Server, Document

from django.db.models.signals import post_save, pre_delete

from mygpo.core.models import Podcast, PodcastGroup
from mygpo.log import log

"""
This module contains methods for converting objects from the old
ORM-based backend to the CouchDB-based backend
"""


def use_couchdb():
    """
    Decorator that connects to the CouchDB-Server before the decorated
    function is called.
    """
    def wrapper(fn):
        def _tmp(*args, **kwargs):
            server = Server()
            db = server.get_or_create_db("mygpo")
            Document.set_db(db)
            return fn(*args, **kwargs)

        return _tmp

    return wrapper


@use_couchdb()
def save_podcast_signal(sender, instance=False, **kwargs):
    """
    Signal-handler for creating/updating a CouchDB-based podcast when
    an ORM-based podcast has been saved
    """
    if not instance:
        return

    try:
        newp = Podcast.for_oldid(instance.id)
        if newp:
            update_podcast(instance, newp)
        else:
            create_podcast(instance)

    except Exception, e:
        log('error while updating CouchDB-Podcast: %s' % repr(e))


@use_couchdb()
def delete_podcast_signal(sender, instance=False, **kwargs):
    """
    Signal-handler for deleting a CouchDB-based podcast when an ORM-based
    podcast is deleted
    """
    if not instance:
        return

    try:
        newp = Podcast.for_oldid(instance.id)
        if newp:
            newp.delete()

    except Exception, e:
        log('error while deleting CouchDB-Podcast: %s' % repr(e))


def update_podcast(oldp, newp):
    """
    Updates newp based on oldp and returns True if an update was necessary
    """
    if oldp.group:
        group = get_group(oldp.group.id)
        if not newp in list(group.podcasts):
            group.add_podcast(newp)
            return True

    return False


def create_podcast(oldp):
    """
    Creates a (CouchDB) Podcast document from a (ORM) Podcast object
    """
    p = Podcast()
    p.oldid = oldp.id
    p.save()

    if oldp.group:
       group = get_group(oldp.group.id)
       group.add_podcast(p)

    return p


def get_group(oldid):
    group = PodcastGroup.for_oldid(oldid)
    if not group:
        group = create_podcastgroup(oldid)

    return group


def create_podcastgroup(oldid):
    """
    Creates a (CouchDB) PodcastGroup document from a
    (ORM) PodcastGroup object
    """
    g = PodcastGroup()
    g.oldid = oldid
    g.save()
    return g
