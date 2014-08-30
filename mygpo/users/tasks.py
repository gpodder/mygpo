from datetime import datetime, timedelta
from itertools import chain
from operator import itemgetter
from collections import Counter

from celery.decorators import periodic_task

from django.contrib.auth import get_user_model
from django.conf import settings

from mygpo.celery import celery
from mygpo.db.couchdb.user import suggestions_for_user, update_suggestions
from mygpo.subscriptions import get_subscribed_podcasts

from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)


@celery.task(max_retries=5, default_retry_delay=60)
def sync_user(user):
    """ Syncs all of the user's sync groups """
    from mygpo.users.models import SubscriptionException

    groups = SyncGroup.objects.filter(user=user)
    for group in groups:

        try:
            group.sync()

        except SubscriptionException:
            # no need to retry on SubscriptionException
            pass

        except Exception as e:
            logger.exception('retrying task')
            raise sync_user.retry()


@celery.task(max_retries=5, default_retry_delay=60)
def update_suggestions(user, max_suggestions=15):
    """ updates the suggestions of a user """

    # get suggestions object
    suggestion = suggestions_for_user(user)

    # calculate possible suggestions
    subscribed_podcasts = get_subscribed_podcasts()
    related = chain.from_iterable([p.related_podcasts for p in subscribed_podcasts])

    # filter out blacklisted podcasts
    related = filter(lambda pid: not pid in suggestion.blacklist, related)

    # get most relevant
    counter = Counter(related)
    get_podcast_id = itemgetter(0)
    suggested = map(get_podcast_id, counter.most_common(max_suggestions))
    update_suggestions(suggestion, suggested)


@periodic_task(run_every=timedelta(hours=1))
def remove_unactivated_users():
    """ Remove users that have not been activated """
    User = get_user_model()
    valid_days = settings.ACTIVATION_VALID_DAYS
    remove_before = datetime.utcnow() - timedelta(days=valid_days)
    logger.warn('Removing unactivated users before %s', remove_before)

    users = User.objects.filter(is_active=False, date_joined__lt=remove_before)
    logger.warn('Removing %d unactivated users', users.count())

    users.delete()
