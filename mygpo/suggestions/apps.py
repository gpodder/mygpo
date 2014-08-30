from django.apps import AppConfig
from django.db.models.signals import post_save

from mygpo.subscriptions.signals import subscription_changed
from mygpo.suggestions.signals import update_suggestions_on_subscription


class UsersConfig(AppConfig):
    name = 'mygpo.suggestions'
    verbose_name = "Suggestions"

    def ready(self):
        subscription_changed.connect(update_suggestions_on_subscription)
