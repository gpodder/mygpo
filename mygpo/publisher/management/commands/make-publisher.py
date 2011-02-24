import sys

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from mygpo.decorators import repeat_on_conflict
from mygpo.core.models import Podcast
from mygpo import migrate


class Command(BaseCommand):
    """
    Makes the specified user a publisher for the specified podcast.

    The user is specified by its username, the podcast is specified by one of
    its URLs.
    """

    def handle(self, *args, **options):

        if len(args) < 2:
            print >> sys.stderr, 'Usage: ./manage.py make-publisher <username> <podcast-url-1> [<podcast-url-2> ...]'
            return

        username = args[0]

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            print >> sys.stderr, 'User %s does not exist' % username
            return
        user = migrate.get_or_migrate_user(user)


        urls = args[1:]
        podcasts = map(Podcast.for_url, urls)
        ids = map(Podcast.get_id, podcasts)
        self.add_publisher(user=user, ids=ids)

    @repeat_on_conflict(['user'])
    def add_publisher(self, user, ids):
        user.published_objects = list(set(user.published_objects + ids))
        user.save()
