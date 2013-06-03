from mygpo.cel import celery
from mygpo.api.advanced import update_episodes


@celery.task(max_retries=5, default_retry_delay=60)
def import_episode_actions(user, actions, upload_ts, ua_string):
    update_episodes(user, actions, upload_ts, ua_string)

# celery-based handler for episode-actions
episode_actions_celery_handler = import_episode_actions.delay
