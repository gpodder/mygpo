from django.core.management.base import BaseCommand
from mygpo.data.historic import calc_podcast
from mygpo.api.models import Podcast
from django.contrib.auth.models import User
from mygpo.publisher.models import PodcastPublisher

class Command(BaseCommand):
    def handle(self, *args, **options):

        username = args[0]
        podcast_url = args[1]

        user = User.objects.get(username=username)
        podcast = Podcast.objects.get(url=podcast_url)

        PodcastPublisher.objects.create(user=user, podcast=podcast)

