from django.apps import AppConfig
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save

from mygpo.users.models import create_missing_profile


class UsersConfig(AppConfig):
    name = 'mygpo.users'
    verbose_name = "Users and Clients"

    def ready(self):
        User = get_user_model()
        post_save.connect(create_missing_profile, sender=User)
