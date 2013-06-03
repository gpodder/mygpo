from mygpo.core.signals import subscription_changed
from mygpo.users.tasks import sync_user, update_suggestions


def sync_user_on_subscription(sender, **kwargs):
    """ synchronizes the user after one of his subscriptions has changed """
    user = kwargs['user']
    sync_user.delay(user)


subscription_changed.connect(sync_user_on_subscription,
                             dispatch_uid='sync_user_on_subscription')


def update_suggestions_on_subscription(sender, **kwargs):
    """ update a user's suggestions after one of his subscriptions change """
    user = kwargs['user']
    update_suggestions.delay(user)


subscription_changed.connect(update_suggestions_on_subscription,
                             dispatch_uid='update_suggestions_on_subscription')
