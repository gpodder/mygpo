from celery.utils.log import get_task_logger
from django_db_geventpool.utils import close_connection
from celery import shared_task

from mygpo.celery import celery
from mygpo.history.models import EpisodeHistoryEntry
from mygpo.episodestates.models import EpisodeState

logger = get_task_logger(__name__)


@shared_task
@close_connection
def update_episode_state(historyentry_pk):
    """Updates the episode state with the saved EpisodeHistoryEntry"""

    # previously an EpisodeHistoryEntry was passed as parameters directly;
    # as there can still be tasks like this in the queue, we should still
    # be able to handle it
    if isinstance(historyentry_pk, EpisodeHistoryEntry):
        historyentry = historyentry_pk
    else:
        historyentry = EpisodeHistoryEntry.objects.get(pk=historyentry_pk)

    user = historyentry.user
    episode = historyentry.episode

    logger.info(
        "Updating Episode State for {user} / {episode}".format(
            user=user, episode=episode
        )
    )

    state = EpisodeState.objects.update_or_create(
        user=user,
        episode=episode,
        defaults={"action": historyentry.action, "timestamp": historyentry.timestamp},
    )
