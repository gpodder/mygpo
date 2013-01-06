from datetime import datetime

from mygpo.core.models import SubscriberData
from mygpo.cel import celery
from mygpo.data.feeddownloader import PodcastUpdater
from mygpo.db.couchdb.podcast import podcast_by_id, subscriberdata_for_podcast
from mygpo.db.couchdb.podcast_state import podcast_subscriber_count


@celery.task(max_retries=5)
def update_podcast_subscribers(podcast_id):
    """ Updates the subscriber count of a podcast """

    try:
        podcast = podcast_by_id(podcast_id)

        # calculate current number of subscribers
        subscriber_count = podcast_subscriber_count(podcast)
        subs_cur = SubscriberData(timestamp=datetime.utcnow(),
                subscriber_count=subscriber_count)

        # sort all subscriber data entries
        subs_all = sorted(podcast.subscribers + [subs_cur],
                key=lambda e: e.timestamp)

        # move all but latest two to history
        subs_history = subscriberdata_for_podcast(podcast_id)
        subs_history.subscribers = subs_all[:-2]
        subs_history.save()

        # move latest two to podcast
        podcast.subscribers = subs_all[-2:]
        podcast.save()

    #TODO: which exceptions?
    except Exception as ex:
        raise update_podcast_subscribers.retry(exc=ex)
