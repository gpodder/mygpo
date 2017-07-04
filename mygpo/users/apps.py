from django.apps import AppConfig, apps
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save


def create_missing_profile(sender, **kwargs):
    """ Creates a UserProfile if a User doesn't have one """
    user = kwargs['instance']

    if not hasattr(user, 'profile'):
        UserProfile = apps.get_model('users.UserProfile')
        profile = UserProfile.objects.create(user=user)
        user.profile = profile


class UsersConfig(AppConfig):
    name = 'mygpo.users'
    verbose_name = "Users and Clients"

    def ready(self):
        User = get_user_model()
        post_save.connect(create_missing_profile, sender=User)
