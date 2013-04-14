from mygpo.cel import celery


@celery.task(max_retries=5, default_retry_delay=60)
def sync_user(user):
    """ Syncs all of the user's device groups """

    for group in user.get_grouped_devices():
        if group.is_synced:
            device = group.devices[0]
            user.sync_group(device)
