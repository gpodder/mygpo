from django.core.management.base import BaseCommand

from mygpo import migrate
from mygpo.utils import progress
from mygpo.api.models.users import EpisodeFavorite
from mygpo.core import models as models


class Command(BaseCommand):


    def handle(self, *args, **options):

        favorites = EpisodeFavorite.objects.all()
        total = favorites.count()

        for n, fav in enumerate(favorites):
            episode = migrate.get_or_migrate_episode(fav.episode)
            podcast = migrate.get_or_migrate_podcast(fav.episode.podcast)
            podcast_state = models.PodcastUserState.for_user_podcast(fav.user, podcast)
            episode_state = podcast_state.get_episode(episode.id)

            episode_state.set_favorite()
            podcast_state.save()

            progress(n+1, total)
