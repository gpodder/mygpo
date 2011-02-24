from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from mygpo import migrate
from mygpo.decorators import repeat_on_conflict
from mygpo.utils import progress
from mygpo.publisher.models import PodcastPublisher


class Command(BaseCommand):

    def handle(self, *args, **options):

        publisher = PodcastPublisher.objects.all()
        total = publisher.count()

        for n, pub in enumerate(publisher.iterator()):
            podcast = migrate.get_or_migrate_podcast(pub.podcast)
            user = migrate.get_or_migrate_user(pub.user)

            self.add_publisher(user=user, id=podcast.get_id())

            progress(n+1, total)


    @repeat_on_conflict(['user'])
    def add_publisher(self, user, id):
        user.published_objects = list(set(user.published_objects + [id]))
        user.save()
