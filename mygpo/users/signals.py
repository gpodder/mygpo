from mygpo.subscriptions.signals import subscription_changed
from mygpo.users.tasks import sync_user


def sync_user_on_subscription(sender, **kwargs):
    """ synchronizes the user after one of his subscriptions has changed """
    user = kwargs['user']
    sync_user.delay(user.pk)


subscription_changed.connect(sync_user_on_subscription,
                             dispatch_uid='sync_user_on_subscription')
