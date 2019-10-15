from mygpo.podcasts.models import Podcast
from mygpo.subscriptions.models import Subscription
from mygpo.celery import celery


@celery.task(max_retries=5)
def update_podcast_subscribers(podcast_id):
    """ Updates the subscriber count of a podcast """

    try:
        podcast = Podcast.objects.get(id=podcast_id)

        # calculate current number of subscribers
        podcast.subscribers = (
            Subscription.objects.filter(podcast=podcast)
            .order_by('user')
            .distinct('user')
            .count()
        )
        podcast.save()

    # TODO: which exceptions?
    except Exception as ex:
        raise update_podcast_subscribers.retry(exc=ex)
