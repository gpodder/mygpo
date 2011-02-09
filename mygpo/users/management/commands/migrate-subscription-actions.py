from optparse import make_option

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from mygpo import migrate
from mygpo.decorators import repeat_on_conflict
from mygpo.utils import progress
from mygpo.api import models


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--min-id', action='store', type="int", dest='min_id', default=0, help="Id from which the migration should start."),
        make_option('--max-id', action='store', type="int", dest='max_id', help="Id at which the migration should end."),
    )


    def handle(self, *args, **options):

        user, old_podcast = None, None
        min_id = options.get('min_id', 0)
        max_id = options.get('max_id', models.EpisodeAction.objects.order_by('-id')[0].id)

        actions = models.SubscriptionAction.objects.filter(id__gte=min_id, id__lte=max_id)
        combinations = list(set(actions.values_list('device__user', 'podcast')))
        total = len(combinations)

        for n, (user_id, podcast_id) in enumerate(combinations):
            user = self.check_new(user, User, user_id)
            old_podcast = self.check_new(old_podcast, models.Podcast, podcast_id)

            self.migrate_for_user_podcast(user, old_podcast)
            progress(n+1, total)


    @repeat_on_conflict()
    def migrate_for_user_podcast(self, user, old_podcast):
        podcast = migrate.get_or_migrate_podcast(old_podcast)
        podcast_state = podcast.get_user_state(user)

        actions = models.SubscriptionAction.objects.filter(device__user=user, podcast=old_podcast).order_by('timestamp')
        for action in actions:
            podcast_state.add_actions([migrate.migrate_subscription_action(action)])

        podcast_state.save()


    def check_new(self, obj, cls, obj_id):
        """
        Checks if obj is the object referred to by obj_id. If it is, the
        object is returned. If not, the object is loaded from the database
        (assumed to be of class cls) and returned
        """
        if not obj or obj.id != obj_id:
            return cls.objects.get(id=obj_id)
        else:
            return obj
