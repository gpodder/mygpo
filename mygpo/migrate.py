from datetime import datetime
from couchdbkit import Server, Document

from mygpo.core.models import Podcast, PodcastGroup, Episode, SubscriberData
from mygpo.users.models import Rating, EpisodeAction, User, Device, SubscriptionAction, EpisodeUserState, PodcastUserState
from mygpo.log import log
from mygpo import utils
from mygpo.decorators import repeat_on_conflict

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
            update_podcast(oldp=instance, newp=newp)
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



def save_device_signal(sender, instance=False, **kwargs):

    if not instance:
        return

    dev = get_or_migrate_device(instance)
    d = update_device(instance, dev)
    user = get_or_migrate_user(instance.user)

    @repeat_on_conflict(['user'])
    def set_device(user, device):
        user.set_device(d)
        user.save()

    set_device(user=user, device=d)

    podcast_states = PodcastUserState.for_user(instance.user)
    for state in podcast_states:

        @repeat_on_conflict(['state'])
        def update_state(state):
            if not state.ref_url:
                podcast = Podcast.get(state.podcast)
                if not podcast or not podcast.url:
                    return
                state.ref_url = podcast.url

            state.set_device_state(dev)
            state.save()

        update_state(state=state)


def delete_device_signal(sender, instance=False, **kwargs):
    if not instance:
        return

    user = get_or_migrate_user(instance.user)
    dev = get_or_migrate_device(instance, user=user)
    user.remove_device(dev)
    user.save()



def save_episode_signal(sender, instance=False, **kwargs):
    """
    Signal-handler for creating/updating a CouchDB-based episode when
    an ORM-based episode has been saved
    """
    if not instance:
        return

    try:
        newe = Episode.for_oldid(instance.id)

        if newe:
            update_episode(instance, newe)
        else:
            create_episode(instance)

    except Exception, e:
        log('error while updating CouchDB Episode: %s' % repr(e))



def delete_episode_signal(sender, instance=False, **kwargs):
    """
    Signal-handler for deleting a CouchDB-based episode when an ORM-based
    episode is deleted
    """
    if not instance:
        return

    try:
        newe = Episode.for_oldid(instance.id)
        if newe:
            newe.delete()

    except Exception, e:
        log('error while deleting CouchDB-Episode: %s' % repr(e))




@repeat_on_conflict(['newp'], reload_f=lambda x: Podcast.get(x.get_id()))
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
        group = get_group(oldp.group)
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

    PROPERTIES = ('language', 'content_types', 'title',
        'description', 'link', 'last_update', 'logo_url',
        'author', 'group_member_name')

    for p in PROPERTIES:
        if getattr(newp, p, None) != getattr(oldp, p, None):
            setattr(newp, p, getattr(oldp, p, None))
            updated = True

    if not oldp.url in newp.urls:
        newp.urls.append(oldp.url)
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
        update_podcast(oldp=oldp, newp=p)

    return p


def get_group(oldg):
    group = PodcastGroup.for_oldid(oldg.id)
    if not group:
        group = create_podcastgroup(oldg)

    return group


def create_podcastgroup(oldg):
    """
    Creates a (CouchDB) PodcastGroup document from a
    (ORM) PodcastGroup object
    """
    g = PodcastGroup()
    g.oldid = oldg.id
    update_podcastgroup(oldg, g)
    g.save()
    return g



@repeat_on_conflict(['newg'])
def update_podcastgroup(oldg, newg):

    if newg.title != oldg.title:
        newg.title = oldg.title
        newg.save()
        return True

    return False


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
    a.total = action.total
    return a

def create_episode(olde, sparse=False):
    podcast = get_or_migrate_podcast(olde.podcast)
    e = Episode()
    e.oldid = olde.id
    e.urls.append(olde.url)
    e.podcast = podcast.get_id()

    if not sparse:
        update_episode(olde, e)

    e.save()

    return e


def get_or_migrate_episode(olde):
    return Episode.for_oldid(olde.id) or create_episode(olde)


def update_episode(olde, newe):
    updated = False

    if not olde.url in newe.urls:
        newe.urls.append(olde.url)
        updated = False

    PROPERTIES = ('title', 'description', 'link',
        'author', 'duration', 'filesize', 'language',
        'last_update')

    for p in PROPERTIES:
        if getattr(newe, p, None) != getattr(olde, p, None):
            setattr(newe, p, getattr(olde, p, None))
            updated = True

    if newe.outdated != olde.outdated:
        newe.outdated = bool(olde.outdated)
        updated = True

    if newe.released != olde.timestamp:
        newe.released = olde.timestamp
        updated = True

    if olde.mimetype and not olde.mimetype in newe.mimetypes:
        newe.mimetypes.append(olde.mimetype)
        updated = True

    @repeat_on_conflict(['newe'])
    def save(newe):
        newe.save()

    if updated:
        save(newe=newe)

    return updated


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
    return Device.for_oldid(device.id) or create_device(device, user=user)


def create_device(oldd, sparse=False, user=None):
    user = user or get_or_migrate_user(oldd.user)

    d = Device()
    d.oldid = oldd.id

    if not sparse:
        update_device(oldd, d)

    user.devices.append(d)
    user.save()
    return d


def update_device(oldd, newd):
    newd.uid = oldd.uid
    newd.name = oldd.name
    newd.type = oldd.type
    newd.deleted = bool(oldd.deleted)
    return newd


def migrate_subscription_action(old_action):
    action = SubscriptionAction()
    action.timestamp = old_action.timestamp
    action.action = 'subscribe' if old_action.action == 1 else 'unsubscribe'
    action.device = get_or_migrate_device(old_action.device).id
    return action


def get_episode_user_state(user, episode, podcast):
    e_state = EpisodeUserState.for_user_episode(user, episode)

    if e_state is None:

        p_state = PodcastUserState.for_user_podcast(user, podcast)
        e_state = p_state.episodes.get(episode._id, None)

        if e_state is None:
            e_state = EpisodeUserState()
            e_state.episode = episode._id
        else:
            @repeat_on_conflict(['p_state'])
            def remove_episode_status(p_state):
                del p_state.episodes[episode._id]
                p_state.save()

            remove_episode_status(p_state=p_state)


    if not e_state.podcast_ref_url:
        e_state.podcast_ref_url = podcast.url

    if not e_state.ref_url:
        e_state.ref_url = episode.url

    e_state.podcast = podcast.get_id()
    e_state.user_oldid = user.id
    e_state.save()

    return e_state


def get_devices(user):
    from mygpo.api.models import Device
    return [get_or_migrate_device(dev) for dev in Device.objects.filter(user=user)]
