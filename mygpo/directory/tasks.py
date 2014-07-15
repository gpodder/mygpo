from mygpo.podcasts.models import Podcast
from mygpo.celery import celery
from mygpo.db.couchdb.podcast_state import podcast_subscriber_count


@celery.task(max_retries=5)
def update_podcast_subscribers(podcast_id):
    """ Updates the subscriber count of a podcast """

    try:
        podcast = Podcast.objects.get(id=podcast_id)

        # calculate current number of subscribers
        subscriber_count = podcast_subscriber_count(podcast)
        podcast.subscribers = subscriber_count
        podcast.save()

    #TODO: which exceptions?
    except Exception as ex:
        raise update_podcast_subscribers.retry(exc=ex)
