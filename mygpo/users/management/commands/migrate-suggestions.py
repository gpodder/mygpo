from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from mygpo.core.models import Podcast
from mygpo.users.models import Suggestions, Rating
from mygpo.data.models import SuggestionBlacklist
from mygpo.web import models as webmodels
from mygpo import migrate
from mygpo.utils import progress
from mygpo.migrate import get_blacklist, get_ratings


class Command(BaseCommand):

    def handle(self, *args, **options):
        updated = 0

        users = User.objects.all()
        total = users.count()
        for n, user in enumerate(users.iterator()):
            blacklist = SuggestionBlacklist.objects.filter(user=user)
            ratings = webmodels.Rating.objects.filter(user=user)

            user = migrate.get_or_migrate_user(user)

            suggestion = Suggestions.for_user(user)
            suggestion.blacklist = migrate.get_blacklist(blacklist)
            suggestion.ratings = migrate.get_ratings(ratings)

            if suggestion.blacklist or suggestion.ratings:
                suggestion.save()
                updated += 1

            status_str = '%d upd' % (updated)
            progress(n, total, status_str)
