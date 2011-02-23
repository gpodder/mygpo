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

            if not user._id in podcast.publisher:
                self.add_publisher(podcast=podcast, user_id=user._id)

            progress(n+1, total)


    @repeat_on_conflict(['podcast'], reload_f=lambda x: Podcast.get(x.get_id()))
    def add_publisher(self, podcast, user_id):
        podcast.publisher.append(user_id)
        podcast.save()
