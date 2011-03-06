from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from mygpo.web.models import SecurityToken

from mygpo import migrate
from mygpo.utils import progress, multi_request_view
from mygpo.core.models import Podcast, PodcastSubscriberData
from mygpo.decorators import repeat_on_conflict


class Command(BaseCommand):
    """
    Migrates tokens from relational SecurityToken models to
    the User objects in the CouchDB backend.
    """

    def handle(self, *args, **options):

        tokens = SecurityToken.objects.all()
        total = tokens.count()

        for n, token in enumerate(tokens):

            try:
                user = User.objects.get(id=token.user_id)
            except User.DoesNotExist:
                pass

            new_user = migrate.get_or_migrate_user(user)

            self.update_user(user=new_user, token=token)

            progress(n+1, total)


    @repeat_on_conflict(['user'])
    def update_user(self, user, token):
        if token.object == 'subscriptions':
            user.subscriptions_token = token.token

        elif token.object == 'fav-feed':
            user.favorite_feed_token = token.token

        elif token.object == 'published_feeds':
            user.publisher_update_token = token.token

        user.save()
