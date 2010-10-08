from mygpo.core.models import Podcast, PodcastGroup
from django.db.models.signals import post_save, pre_delete

"""
This module contains methods for converting objects from the old
ORM-based backend to the CouchDB-based backend
"""

def save_podcast_signal(sender, instance=False, **kwargs):
    """
    Signal-handler for creating/updating a CouchDB-based podcast when
    an ORM-based podcast has been saved
    """
    if not instance:
        return

    newp = Podcast.for_oldid(instance.id)
    if newp:
        update_podcast(instance, newp)
    else:
        create_podcast(instance)


def delete_podcast_signal(sender, instance=False, **kwargs):
    """
    Signal-handler for deleting a CouchDB-based podcast when an ORM-based
    podcast is deleted
    """
    if not instance:
        return

    newp = Podcast.for_oldid(instance.id)
    if newp:
        newp.delete()


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
