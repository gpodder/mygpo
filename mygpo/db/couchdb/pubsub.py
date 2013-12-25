from couchdbkit import MultipleResultsFound

from mygpo.pubsub.models import Subscription
from mygpo.db.couchdb import get_pubsub_database
from mygpo.decorators import repeat_on_conflict


def subscription_for_topic(topic):
    """ return the subscription for the given topic, one None """

    db = get_pubsub_database()
    _view = 'subscriptions/by_topic'

    r = db.view(_view,
            key          = topic,
            include_docs = True,
            reduce       = False,
            schema       = Subscription
        )

    if r:
        try:
            sub = r.one()
        except MultipleResultsFound as ex:
            logger.exception('Multiple results found in %s with params %s',
                             _view, r.params)
            sub = r.first()

        sub.set_db(db)
        return sub

    if r:
        try:
            podcast_group = r.one()
        except MultipleResultsFound as ex:
            logger.exception('Multiple results found in %s with params %s',
                             _view, r.params)
            podcast_group = r.first()


    else:
        return None


@repeat_on_conflict(['subscription'])
def set_subscription_verified(subscription):
    """ marks the pubsub subscription as verified """
    pdb = get_pubsub_database()
    subscription.verified = True
    pdb.save_doc(subscription)
