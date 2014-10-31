import sys

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from mygpo.podcasts.models import Podcast
from mygpo.publisher.models import PublishedPodcast


class Command(BaseCommand):
    """
    Makes the specified user a publisher for the specified podcast.

    The user is specified by its username, the podcast is specified by one of
    its URLs.
    """

    def handle(self, *args, **options):

        if len(args) < 2:
            print('Usage: ./manage.py make-publisher <username> <podcast-url-1> [<podcast-url-2> ...]', file=sys.stderr)
            return

        username = args[0]

        User = get_user_model()
        user = User.objects.get(username=username)
        if not user:
            print('User %s does not exist' % username, file=sys.stderr)
            return

        urls = args[1:]
        podcasts = Podcast.objects.filter(urls__url__in=urls)
        PublishedPodcast.objects.get_or_create(user, podcasts)
