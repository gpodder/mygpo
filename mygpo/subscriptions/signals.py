import django.dispatch

# indicates that a podcast was subscribed or unsubscribed
# ``sender`` will equal the user. Additionally the parameters ``user`` and
# ``subscribed`` will be provided
subscription_changed = django.dispatch.Signal()
