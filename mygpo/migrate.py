from couchdbkit import Server, Document

from django.db.models.signals import post_save, pre_delete

from mygpo.core.models import Podcast, PodcastGroup, Rating
from mygpo.log import log

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

    try:
        newp = Podcast.for_oldid(instance.id)
        if newp:
            update_podcast(instance, newp)
        else:
            create_podcast(instance)

    except Exception, e:
        log('error while updating CouchDB-Podcast: %s' % repr(e))


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

    updated = False

    if oldp.group:
        group = get_group(oldp.group.id)
        if not newp in list(group.podcasts):
            group.add_podcast(newp)
            updated = True

    # Update related podcasts
    from mygpo.data.models import RelatedPodcast
    rel_podcast = set([r.rel_podcast for r in RelatedPodcast.objects.filter(ref_podcast=oldp)])
    rel = list(podcasts_to_ids(rel_podcast))
    if newp.related_podcasts != rel:
        newp.related_podcasts = rel
        updated = True

    if updated:
        newp.save()

    return updated


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


def get_blacklist(blacklist):
    """
    Returns a list of Ids of all blacklisted podcasts
    """
    blacklisted = [b.podcast for b in blacklist]
    blacklist_ids = []
    for p in blacklisted:
        newp = Podcast.for_oldid(p.id)
        if not newp:
            newp = create_podcast(p)

        blacklist_ids.append(newp._id)
    return blacklist_ids


def get_ratings(ratings):
    """
    Returns a list of Rating-objects, based on the relational Ratings
    """
    conv = lambda r: Rating(rating=r.rating, timestamp=r.timestamp)
    return map(conv, ratings)


def podcasts_to_ids(podcasts):
    for p in podcasts:
        podcast = Podcast.for_oldid(p.id)
        if not podcast:
            podcast = create_podcast(p)
        yield podcast.get_id()


def get_or_migrate_podcast(oldp):
    return Podcast.for_oldid(oldp.id) or create_podcast(oldp)
