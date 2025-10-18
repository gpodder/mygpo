from datetime import datetime, timedelta
from importlib import import_module

from celery import shared_task
from django_db_geventpool.utils import close_connection

from django.contrib.auth import get_user_model
from django.conf import settings

from . import models

from celery.utils.log import get_task_logger

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
          logger.warning('Would delete %d clients of ARCHIVED user "%s" at "%s"', len(clients), user.username, user.profile.archive_path)
        elif clients:
          logger.warning('Would delete %d clients of user "%s" joined %s last_login %s', len(clients), user.username, user.date_joined, user.last_login)
        else:
          logger.info('Would delete user "%s" joined %s last_login %s without client', user.username, user.date_joined, user.last_login)


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
