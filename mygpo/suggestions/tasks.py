from itertools import chain
from operator import itemgetter
from collections import Counter

from mygpo.celery import celery
from mygpo.db.couchdb.user import (suggestions_for_user,
    update_suggestions as update)
from mygpo.subscriptions import get_subscribed_podcasts

from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)


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
    update(suggestion, suggested)
