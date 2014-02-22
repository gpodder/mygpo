from couchdbkit import MultipleResultsFound

from mygpo.pubsub.models import Subscription
from mygpo.db.couchdb import get_pubsub_database, get_single_result
from mygpo.decorators import repeat_on_conflict

import logging
logger = logging.getLogger(__name__)


def subscription_for_topic(topic):
    """ return the subscription for the given topic, one None """

    db = get_pubsub_database()
    sub = get_single_result(db, 'subscriptions/by_topic',
            key          = topic,
            include_docs = True,
            reduce       = False,
            schema       = Subscription
        )

    return sub


@repeat_on_conflict(['subscription'])
def set_subscription_verified(subscription):
    """ marks the pubsub subscription as verified """
    pdb = get_pubsub_database()
    subscription.verified = True
    pdb.save_doc(subscription)
