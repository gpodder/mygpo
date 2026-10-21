import os
from datetime import datetime, timedelta
from importlib import import_module

from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django_db_geventpool.utils import close_connection

from mygpo.users.models import UserArchive
from mygpo.users.archiver import UserArchiver

from . import models

logger = get_task_logger(__name__)


@shared_task(max_retries=5, default_retry_delay=60)
@close_connection
def sync_user(user_pk):
    """Syncs all of the user's sync groups"""
    from mygpo.users.models import SubscriptionException

    User = get_user_model()
    user = User.objects.get(pk=user_pk)

    groups = models.SyncGroup.objects.filter(user=user)
    for group in groups:
        try:
            group.sync()

        except SubscriptionException:
            # no need to retry on SubscriptionException
            pass

        except Exception:
            logger.exception("retrying task")
            raise sync_user.retry()


@shared_task(run_every=timedelta(hours=1))
@close_connection
def remove_inactive_users():
    """Remove users that have not been activated"""
    User = get_user_model()

    # time for which to keep unactivated and deleted users
    valid_days = settings.ACTIVATION_VALID_DAYS
    remove_before = datetime.utcnow() - timedelta(days=valid_days)
    logger.warning("Removing unactivated users before %s", remove_before)

    users = User.objects.filter(
        is_active=False,
        date_joined__lt=remove_before,
        profile__archived_date__isnull=True,
    )

    for user in users:
        clients = models.Client.objects.filter(user=user)
        if user.profile.archive_path:
            logger.warning(
                'Would delete %d clients of ARCHIVED user "%s" at "%s"',
                len(clients),
                user.username,
                user.profile.archive_path,
            )
        elif clients:
            logger.warning(
                'Would delete %d clients of user "%s" joined %s last_login %s',
                len(clients),
                user.username,
                user.date_joined,
                user.last_login,
            )
        else:
            logger.info(
                'Would delete user "%s" joined %s last_login %s without client',
                user.username,
                user.date_joined,
                user.last_login,
            )


#        logger.warning('Deleting %d clients of user "%s"', len(clients), user.username)
#        clients.delete()
#        logger.warning('Deleting user "%s"', user.username)
#        user.delete()


@shared_task(run_every=timedelta(hours=1))
@close_connection
def clearsessions():
    """Clear expired sessions

    This runs code that should normally be run by ``manage.py clearsessions``.
    If Django's internals change, see
    django/contrib/sessions/management/commands/clearsessions.py for the
    current implementation."""

    engine = import_module(settings.SESSION_ENGINE)
    engine.SessionStore.clear_expired()


@shared_task
@close_connection
def generate_archive(archive_id):
    """Generates a new archive"""

    archive = UserArchive.objects.get(id=archive_id)
    user = archive.user

    if archive.path:
        logger.warning(
            "Archive %s for user %s (%s) already generated",
            archive_id,
            user.username,
            user.id,
        )
        return

    archive_dest = os.path.join(
        settings.ARCHIVE_ROOT, f"{user.id}-{archive.id}.tar.zst"
    )

    if not os.path.exists(os.path.dirname(archive_dest)):
        raise Exception(f"archive {archive_dest} parent directory doesn't exist")

    output_dir = os.path.join(settings.ARCHIVE_ROOT, f"work-{archive.id}")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    else:
        raise Exception(
            f"output_dir {output_dir} exists, maybe another archival in parallel"
        )

    logger.info(
        "archiving user %s (archive_id=%s) output_dir=%s",
        user.username,
        archive.id,
        output_dir,
    )

    with transaction.atomic():
        archiver = UserArchiver(
            archive=archive, output_dir=output_dir, archive_dest=archive_dest
        )
        archiver.export()

    logger.info(
        "compressing user %s (archive_id=%s) archive output_dir=%s archive_dest=%s",
        user.username,
        archive.id,
        output_dir,
        archive_dest,
    )
    archive_ok = archiver.create_archive()
    if archive_ok:
        archive.path = archive_dest
        archive.save()
        logger.info(
            "Created user %s (archive_id=%s) archive_dest=%s",
            user.username,
            archive.id,
            archive_dest,
        )
    else:
        logger.warning(
            "Failed creating user %s (archive_id=%s) archive_dest=%s",
            user.username,
            archive.id,
            archive_dest,
        )

    archiver.clean_output()
