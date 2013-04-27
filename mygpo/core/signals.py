import django.dispatch

# indicates that an incomplete object has been loaded from the database
# the object needs to be updated from its source (eg the feed)
incomplete_obj = django.dispatch.Signal()


# indicates that a podcast was subscribed or unsubscribed
# ``sender`` will equal the user. Additionally the parameters ``user`` and
# ``subscribed`` will be provided
subscription_changed = django.dispatch.Signal()
