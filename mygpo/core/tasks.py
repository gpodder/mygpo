from datetime import datetime

from django.utils.translation import ugettext as _
from django.conf import settings

from mygpo.cel import celery
from mygpo.data.feeddownloader import PodcastUpdater
from mygpo.utils import get_timestamp
from mygpo.users.models import EpisodeAction
from mygpo.flattr import Flattr
from mygpo.db.couchdb.podcast import podcast_by_id
from mygpo.db.couchdb.episode import episode_by_id
from mygpo.db.couchdb.episode_state import episode_state_for_user_episode, \
         add_episode_actions


@celery.task(max_retries=5, default_retry_delay=60)
def flattr_thing(user, thing_id, domain, thing_type):
    """ Task to flattr a thing """

    flattr = Flattr(user, domain)

    if thing_type == 'Podcast':
        thing = podcast_by_id(thing_id)

    elif thing_type == 'Episode':
        thing = episode_by_id(thing_id)

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

    return success, msg


def auto_flattr_episode(user, episode_id):
    """ Task to auto-flattr an episode

    In addition to the flattring itself, it also records the event """

    success, msg = flattr_thing(user, episode_id, None, 'Episode')

    if not success:
        return False

    episode = episode_by_id(episode_id)
    state = episode_state_for_user_episode(user, episode)

    action = EpisodeAction()
    action.action = 'flattr'
    add_episode_actions(state, [action])

    return True
