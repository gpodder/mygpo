import django.dispatch

# indicates that a PubSubHubbub subscription has been updated by on Hub
subscription_updated = django.dispatch.Signal()
