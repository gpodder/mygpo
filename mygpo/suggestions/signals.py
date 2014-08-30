from mygpo.subscriptions.signals import subscription_changed
from mygpo.suggestions.tasks import update_suggestions


def update_suggestions_on_subscription(sender, **kwargs):
    """ update a user's suggestions after one of his subscriptions change """
    user = kwargs['user']
    update_suggestions.delay(user)


subscription_changed.connect(update_suggestions_on_subscription,
                             dispatch_uid='update_suggestions_on_subscription')
