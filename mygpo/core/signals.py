import django.dispatch

# indicates that an incomplete object has been loaded from the database
# the object needs to be updated from its source (eg the feed)
incomplete_obj = django.dispatch.Signal()
