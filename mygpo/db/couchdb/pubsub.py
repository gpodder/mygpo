from mygpo.pubsub.models import Subscription
from mygpo.db.couchdb import get_pubsub_database


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
