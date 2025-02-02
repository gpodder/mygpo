from django.apps import AppConfig, apps

from mygpo.subscriptions.signals import subscription_changed


def update_suggestions_on_subscription(sender, **kwargs):
    """update a user's suggestions after one of his subscriptions change"""
    from mygpo.suggestions.tasks import update_suggestions

    user = kwargs["user"]


#    update_suggestions.delay(user.pk)


class SuggestionsConfig(AppConfig):
    name = "mygpo.suggestions"
    verbose_name = "Suggestions"

    def ready(self):
        Podcast = apps.get_model("podcasts.Podcast")
        subscription_changed.connect(update_suggestions_on_subscription, sender=Podcast)
