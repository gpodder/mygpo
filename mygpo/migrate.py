from datetime import datetime
from couchdbkit import Server, Document

from mygpo.core.models import Podcast, PodcastGroup, Rating, Episode, EpisodeAction, SubscriberData, User, Device, SubscriptionAction
from mygpo.log import log
from mygpo import utils

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

    # Update related podcasts
    from mygpo.data.models import RelatedPodcast
    if newp._id:
        rel_podcast = set([r.rel_podcast for r in RelatedPodcast.objects.filter(ref_podcast=oldp)])
        rel = list(podcasts_to_ids(rel_podcast))
        if newp.related_podcasts != rel:
            newp.related_podcasts = rel
            updated = True

    # Update Group-assignment
    if oldp.group:
        group = get_group(oldp.group.id)
        if not newp in list(group.podcasts):
            newp = group.add_podcast(newp)
            updated = True

    # Update subscriber-data
    from mygpo.data.models import HistoricPodcastData
    sub = HistoricPodcastData.objects.filter(podcast=oldp).order_by('date')
    if sub.count() and len(newp.subscribers) != sub.count():
        transf = lambda s: SubscriberData(
            timestamp = datetime(s.date.year, s.date.month, s.date.day),
            subscriber_count = s.subscriber_count)
        check = lambda s: s.date.weekday() == 6

        newp.subscribers = newp.subscribers + map(transf, filter(check, sub))
        newp.subscribers = utils.set_cmp(newp.subscribers, lambda x: x.timestamp)
        newp.subscribers = list(sorted(set(newp.subscribers), key=lambda s: s.timestamp))
        updated = True

    # Update Language
    if newp.language != oldp.language:
        newp.language = oldp.language
        updated = True

    # Update content types
    if newp.content_types != oldp.content_types:
        newp.content_types = oldp.content_types
        updated = True

    if updated:
        newp.save()

    return updated


def create_podcast(oldp, sparse=False):
    """
    Creates a (CouchDB) Podcast document from a (ORM) Podcast object
    """
    p = Podcast()
    p.oldid = oldp.id
    p.save()
    if not sparse:
        update_podcast(oldp, p)

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
            podcast = create_podcast(p, sparse=True)
        yield podcast.get_id()


def get_or_migrate_podcast(oldp):
    return Podcast.for_oldid(oldp.id) or create_podcast(oldp)


def create_episode_action(action):
    a = EpisodeAction()
    a.action = action.action
    a.timestamp = action.timestamp
    a.device_oldid = action.device.id if action.device else None
    a.started = action.started
    a.playmark = action.playmark
    return a


def get_or_migrate_episode(episode):
    e = Episode.for_oldid(episode.id)
    if e:
        return e

    podcast = get_or_migrate_podcast(episode.podcast)
    e = Episode()
    e.oldid = episode.id
    e.urls.append(episode.url)
    podcast.episodes[e.id] = e
    podcast.save()
    return e


def get_or_migrate_user(user):
    u = User.for_oldid(user.id)
    if u:
        return u

    u = User()
    u.oldid = user.id
    u.username = user.username
    u.save()
    return u


def get_or_migrate_device(device, user=None):
    d = Device.for_user_uid(device.user, device.uid)
    if d:
        return d

    d = Device()
    d.oldid = device.id
    d.uid = device.uid
    d.name = device.name
    d.type = device.type
    d.deleted = device.deleted
    u = user or get_or_migrate_user(device.user)
    u.devices.append(d)
    u.save()
    return d


def migrate_subscription_action(old_action):
    action = SubscriptionAction()
    action.timestamp = old_action.timestamp
    action.action = 'subscribe' if old_action.action == 1 else 'unsubscribe'
    action.device = get_or_migrate_device(old_action.device).id
    return action
