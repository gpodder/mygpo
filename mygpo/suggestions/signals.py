from mygpo.subscriptions.signals import subscription_changed

subscription_changed.connect(update_suggestions_on_subscription,
                             dispatch_uid='update_suggestions_on_subscription')
