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
        combinations = list(set(actions.values_list('user', 'episode__podcast')))

        docs = []

        total = len(combinations)
        for n, (user_id, podcast_id) in enumerate(combinations):
            user = self.check_new(user, User, user_id)
            podcast = self.check_new(podcast, oldmodels.Podcast, podcast_id)

            docs.append(self.migrate_for_user_podcast(user, podcast, actions))

            progress(n+1, total)

        docs = filter(lambda x: x != None, docs)
        PodcastUserState.save_docs(docs)
        progress(n+1, total, 'saving %d documents' % len(docs))


    def migrate_for_user_podcast(self, user, podcast, actions):
        np = migrate.get_or_migrate_podcast(podcast)
        p_state = PodcastUserState.for_user_podcast(user, np)
        episodes = list(set(actions.filter(user=user, episode__podcast=podcast).values_list('episode', flat=True)))

        orig_len = len(p_state.episodes)

        for episode_id in episodes:
            episode = oldmodels.Episode.objects.get(id=episode_id)

            ne_id = migrate.get_or_migrate_episode(episode).id
            e_state = p_state.get_episode(ne_id)
            e_state.episode_oldid = episode.id
            e_state.add_actions(self.migrate_for_user_episode(user, episode, actions))

            if e_state.actions:
                p_state.episodes[ne_id] = e_state

        if p_state.episodes and len(p_state.episodes) > orig_len:
            return p_state
        return None


    def migrate_for_user_episode(self, user, episode, actions):
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
