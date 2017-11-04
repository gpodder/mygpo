from celery.utils.log import get_task_logger

from django_db_geventpool.utils import close_connection

from mygpo.celery import celery
from mygpo.api.advanced import update_episodes

logger = get_task_logger(__name__)


@celery.task(max_retries=5, default_retry_delay=60)
@close_connection
def import_episode_actions(user, actions, upload_ts, ua_string):
    logger.info('Importing %d tasks for user %s', len(actions), user)
    update_episodes(user, actions, upload_ts, ua_string)

# celery-based handler for episode-actions
episode_actions_celery_handler = import_episode_actions.delay
