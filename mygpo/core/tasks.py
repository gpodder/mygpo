from datetime import datetime

from django.utils.translation import ugettext as _
from django.conf import settings
from django.contrib.auth import get_user_model

from mygpo.podcasts.models import Podcast, Episode
from mygpo.celery import celery
from mygpo.history.models import HistoryEntry
from mygpo.flattr import Flattr
from mygpo.history.models import EpisodeHistoryEntry


User = get_user_model()


@celery.task(max_retries=5, default_retry_delay=60)
def flattr_thing(user_id, thing_id, domain, is_secure, thing_type):
    """ Task to flattr a thing """

    user = User.objects.get(pk=user_id)
    flattr = Flattr(user, domain, is_secure)

    if thing_type == 'Podcast':
        thing = Podcast.objects.get(id=thing_id)
        episode, podcast = None, thing

    elif thing_type == 'Episode':
        query = Episode.objects.filter(id=thing_id).select_related('podcast')
        thing = query.get()
        episode, podcast = thing, thing.podcast

    else:
        raise NotImplemented(_("Can't flattr a '%s'") % thing_type)


    if not thing.flattr_url:
        return False, _('No Payment URL available')

    try:
        success, msg = flattr.flattr_url(thing.flattr_url)

        if settings.FLATTR_MYGPO_THING:
            flattr.flattr_url(settings.FLATTR_MYGPO_THING)

    except Exception as ex:
        raise flattr_thing.retry(exc=ex)

    if success:
        HistoryEntry.objects.create(
            timestamp=datetime.utcnow(),
            podcast=podcast,
            episode=episode,
            user=user,
            client=None,
            action=HistoryEntry.FLATTR,
        )


    return success, msg


@celery.task(max_retries=5, default_retry_delay=60)
def auto_flattr_episode(user_id, episode_id):
    """ Task to auto-flattr an episode

    In addition to the flattring itself, it also records the event """

    success, msg = flattr_thing(user_id, episode_id, None, False, 'Episode')

    if not success:
        return False

    episode = Episode.objects.get(id=episode_id)

    user = User.objects.get(pk=user_id)
    EpisodeHistoryEntry.create_entry(user, episode, EpisodeHistoryEntry.FLATTR)
    return True
