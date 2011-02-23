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


        for podcast_url in args[1:]:

            podcast = Podcast.for_url(podcast_url)
            if podcast is None:
                print >> sys.stderr, 'Podcast with URL %s does not exist. skipping.' % podcast_url
                continue

            self.add_publisher(podcast=podcast, user_id=user._id)
            print >> sys.stderr, 'Made user %s publisher for Podcast %s' % (username, podcast.get_id())


    @repeat_on_conflict(['podcast'], reload_f=lambda x: Podcast.get(x.get_id()))
    def add_publisher(self, podcast, user_id):
        podcast.publisher = list(set(podcast.publisher + [user_id]))
        podcast.save()
