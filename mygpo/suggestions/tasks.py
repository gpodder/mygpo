from itertools import chain
from collections import Counter

from django.contrib.auth import get_user_model

from mygpo.celery import celery
from mygpo.subscriptions import get_subscribed_podcasts
from mygpo.suggestions.models import PodcastSuggestion

from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)


@celery.task
def update_suggestions(user_pk, max_suggestions=15):
    """ updates the suggestions of a user """

    User = get_user_model()
    user = User.objects.get(pk=user_pk)

    logger.info('Updating suggestions of user {user.username}'.format(
        user=user))

    # calculate possible suggestions
    subscribed_podcasts = [sp.podcast for sp in get_subscribed_podcasts(user)]
    logger.debug('Found {num_podcasts} subscribed podcasts'.format(
        num_podcasts=len(subscribed_podcasts)))

    # TODO: update related_podcasts of the subscribed_podcasts?

    related = list(chain.from_iterable([p.related_podcasts.all() for p
                                        in subscribed_podcasts]))

    # get most relevant
    counter = Counter(related)
    logger.debug('Found {num_related} related podcasts'.format(
        num_related=len(counter)))

    suggested = [p for p, count in counter.most_common(max_suggestions)]

    for suggested_podcast in suggested:
        ps, created = PodcastSuggestion.objects.get_or_create(
            suggested_to=user,
            podcast=suggested_podcast,
        )
        if created:
            logger.info('Created suggestion for {podcast}'.format(
                podcast=suggested_podcast))

    user.profile.suggestions_up_to_date = True
    user.profile.save()
