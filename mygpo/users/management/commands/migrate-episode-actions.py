from optparse import make_option

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from mygpo import migrate
from mygpo.utils import progress
from mygpo.api import models as oldmodels
from mygpo.users.models import PodcastUserState


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--min-id', action='store', type="int", dest='min_id', default=0, help="Id from which the migration should start."),
        make_option('--max-id', action='store', type="int", dest='max_id', help="Id at which the migration should end."),
    )


    def handle(self, *args, **options):

        user, podcast = None, None
        min_id = options.get('min_id', 0)
        max_id = options.get('max_id', oldmodels.EpisodeAction.objects.order_by('-id')[0].id)

        actions = oldmodels.EpisodeAction.objects.filter(id__gte=min_id, id__lte=max_id)
        combinations = list(set(actions.values_list('user', 'episode')))

        docs = []

        total = len(combinations)
        for n, (user_id, episode_id) in enumerate(combinations):
            user = self.check_new(user, User, user_id)
            episode = self.check_new(podcast, oldmodels.Episode, episode_id)

            while True:
                try:
                    self.migrate_for_user_episode(user, episode, actions)
                    break
                except:
                    pass

            progress(n+1, total)


    def migrate_for_user_episode(self, user, episode, actions):
        ne = migrate.get_or_migrate_episode(episode)
        np = migrate.get_or_migrate_podcast(episode.podcast)

        e_state = migrate.get_episode_user_state(user, ne._id, np)
        e_state.ref_url = episode.url
        e_state.podcast_ref_url = episode.podcast.url

        orig_len = len(e_state.actions)
        e_state.add_actions(self.get_actions(user, episode, actions))

        if len(e_state.actions) and len(e_state.actions) > orig_len:
            e_state.save()


    def get_actions(self, user, episode, actions):
        actions = actions.filter(user=user, episode=episode).distinct()
        return map(migrate.create_episode_action, actions)

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
