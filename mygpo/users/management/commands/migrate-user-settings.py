from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from mygpo import migrate
from mygpo.decorators import repeat_on_conflict
from mygpo.utils import progress
from mygpo.users.models import PodcastUserState


class Command(BaseCommand):
    """
    Migrates all settings from UserProfile objects into CouchDB-based
    Users.

    All settings are transferred as they are. The semantics of the setting
    'public_profile' changes so that it will act as a default value for new
    subscription's 'public_subscription' setting and not override it anymore.
    """

    def handle(self, *args, **options):

        users = User.objects.all()

        if args:
            users = users.filter(username__in=args)

        total = len(users)

        for n, user in enumerate(users):
            new_user = migrate.get_or_migrate_user(user)
            profile = user.get_profile()

            self.update_user_settings(user=new_user, profile=profile)

            # We change the semantics of public_profile.
            # If a user had a private profile, we set all his subscriptions private
            if (not profile.settings.get('public_profile', True)) or (not profile.public_profile):
                podcast_states = PodcastUserState.for_user(user)
                for state in podcast_states:
                    self.update_subscription_privacy(state=state)

            progress(n+1, total)


    @repeat_on_conflict()
    def update_user_settings(self, user, profile):
        settings = user.settings

        if 'public_profile' in profile.settings:
            settings['public_subscriptions'] = profile.settings['public_profile']
            del profile.settings['public_profile']

        settings.update(profile.settings)
        user.settings = settings
        user.save()

    @repeat_on_conflict()
    def update_subscription_privacy(self, state):
        state.settings['public_subscription'] = False
        state.save()
