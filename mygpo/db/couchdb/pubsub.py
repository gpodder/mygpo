from mygpo.pubsub.models import Subscription
from mygpo.db.couchdb import get_pubsub_database
from mygpo.decorators import repeat_on_conflict


def subscription_for_topic(topic):
    """ return the subscription for the given topic, one None """

    db = get_pubsub_database()

    r = db.view('subscriptions/by_topic',
            key          = topic,
            include_docs = True,
            reduce       = False,
            schema       = Subscription
        )

    if r:
        sub = r.one()
        sub.set_db(db)
        return sub

    else:
        return None


@repeat_on_conflict(['subscription'])
def set_subscription_verified(subscription):
    """ marks the pubsub subscription as verified """
    pdb = get_pubsub_database()
    subscription.verified = True
    pdb.save_doc(subscription)
