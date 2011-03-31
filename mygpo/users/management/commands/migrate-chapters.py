from django.core.management.base import BaseCommand

from mygpo import migrate
from mygpo.utils import progress
from mygpo.api.models.episodes import Chapter
from mygpo.core.models import Episode
from mygpo.users import models


class Command(BaseCommand):
    """ Migrates chapters from the relational backend to CouchDB """

    def handle(self, *args, **options):

        chapters = Chapter.objects.all()
        total = chapters.count()

        for n, chapter in enumerate(chapters):

            user = migrate.get_or_migrate_user(chapter.user)
            episode = migrate.get_or_migrate_episode(chapter.episode)

            if chapter.device:
                device = migrate.get_or_migrate_device(chapter.device)
                device_id = device.id
            else:
                device_id = None

            state = episode.get_user_state(chapter.user)

            n_chapter = models.Chapter()
            n_chapter.created = chapter.created
            n_chapter.start = chapter.start
            n_chapter.end = chapter.end
            n_chapter.label = chapter.label
            n_chapter.advertisement = chapter.advertisement
            n_chapter.device = device_id

            state.update_chapters(add=[n_chapter])

            progress(n+1, total)
