from optparse import make_option

from restkit.errors import Unauthorized

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from mygpo import migrate
from mygpo.decorators import repeat_on_conflict
from mygpo.utils import progress
from mygpo.api import models


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--min-id', action='store', type="int", dest='min_id', default=0, help="Id from which the migration should start."),
        make_option('--max-id', action='store', type="int", dest='max_id', default=None, help="Id at which the migration should end."),
        make_option('--user', action='store', type="string", dest='user', help="Migrate actions for a given user"),
    )


    def handle(self, *args, **options):

        user, old_podcast = None, None
        min_id   = options.get('min_id', 0)
        max_id   = options.get('max_id', models.SubscriptionAction.objects.order_by('-id')[0].id)
        username = options.get('user', None)

        actions = models.SubscriptionAction.objects.order_by('-id')

        if min_id:
            actions = actions.filter(id__gte=min_id)
        if max_id:
            actions = actions.filter(id__lte=max_id)
        if username:
            actions = actions.filter(device__user__username=username)

        total = actions.count()

        for n, action in enumerate(actions):
            try:
                self.migrate_action(action)
            except Unauthorized as e:
                print 'skipping action %d: %s' % (action.id, repr(e))

            progress(n+1, total, str(action.id))


    @repeat_on_conflict()
    def migrate_action(self, action):
        try:
            podcast = action.podcast
            user = action.device.user
        except:
            return

        while True:
            try:
                new_podcast = migrate.get_or_migrate_podcast(podcast)
                migrate.update_podcast(podcast, new_podcast)
                podcast_state = new_podcast.get_user_state(user)
                podcast_state.ref_url = podcast.url

                new_action = migrate.migrate_subscription_action(action)
                podcast_state.add_actions([new_action])

                podcast_state.save()
                break
            except Unauthorized:
                raise
            except Exception as e:
                print repr(e)
