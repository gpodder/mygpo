from django.core.management.base import BaseCommand

from mygpo import migrate
from mygpo.decorators import repeat_on_conflict
from mygpo.utils import progress
from mygpo.api import models


class Command(BaseCommand):


    def handle(self, *args, **options):

        metas = models.SubscriptionMeta.objects.all()

        if args:
            metas = metas.filter(user__username__in=args)

        total = len(metas)

        for n, meta in enumerate(metas):
            podcast = migrate.get_or_migrate_podcast(meta.podcast)
            state = podcast.get_user_state(meta.user)

            self.update_state(state, meta)
            progress(n+1, total)


    @repeat_on_conflict()
    def update_state(self, state, meta):
        settings = state.settings

        # we previously used 'public' to store the public-subscription flag
        # but 'public_subscription' was stated in the API description
        if 'public' in meta.settings:
            settings['public_subscription'] = meta.settings['public']
            del meta.settings['public']

        settings.update(meta.settings)
        state.settings = settings
        state.save()
