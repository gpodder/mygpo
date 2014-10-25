from celery.utils.log import get_task_logger

from mygpo.celery import celery
from mygpo.episodestates.models import EpisodeState

logger = get_task_logger(__name__)


@celery.task
def update_episode_state(historyentry):
    """ Updates the episode state with the saved EpisodeHistoryEntry """

    state = EpisodeState.objects.update_or_create(
        user=historyentry.user,
        episode=historyentry.episode,
        defaults={
            'action': historyentry.action,
            'timestamp': historyentry.timestamp,
        }
    )
