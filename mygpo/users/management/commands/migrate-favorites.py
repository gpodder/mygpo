from django.core.management.base import BaseCommand

from mygpo import migrate
from mygpo.utils import progress
from mygpo.api.models.users import EpisodeFavorite
from mygpo.users.models import PodcastUserState


class Command(BaseCommand):


    def handle(self, *args, **options):

        favorites = EpisodeFavorite.objects.all()
        total = favorites.count()

        for n, fav in enumerate(favorites):
            episode = migrate.get_or_migrate_episode(fav.episode)
            podcast = migrate.get_or_migrate_podcast(fav.episode.podcast)
            episode_state = migrate.get_episode_user_state(fav.user, episode, podcast)

            episode_state.set_favorite()
            episode_state.save()

            progress(n+1, total)
