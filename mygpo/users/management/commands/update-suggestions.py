from itertools import chain
from optparse import make_option

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from mygpo.core.models import Podcast
from mygpo.users.models import Suggestions
from mygpo.api import models
from mygpo import migrate
from mygpo.utils import progress, set_by_frequency


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--max', action='store', type='int', dest='max', default=15, help="Maximum number of suggested podcasts per user."),
        make_option('--max-users', action='store', type='int', dest='max_users', default=15, help="Maximum number of users to update."),
        make_option('--outdated-only', action='store_true', dest='outdated', default=False, help="Update only users where the suggestions are not up-to-date"),
        make_option('--user', action='store', type='string', dest='username', default='', help="Update a specific user"),
        )


    def handle(self, *args, **options):

        max = options.get('max')

        users = User.objects.filter(is_active=True)

        if options.get('outdated'):
            users = users.filter(userprofile__suggestion_up_to_date=False)

        if options.get('username'):
            users = users.filter(username=options.get('username'))

        if options.get('max_users'):
            users = users[:int(options.get('max_users'))]

        total = users.count()

        for n, user in enumerate(users):
            suggestion = Suggestions.for_user_oldid(user.id)

            new_user = migrate.get_or_migrate_user(user)
            subscribed_podcasts = list(set(new_user.get_subscribed_podcasts()))

            related = chain(*[p.related_podcasts for p in subscribed_podcasts])
            related = filter(lambda pid: not pid in suggestion.blacklist, related)
            related = set_by_frequency(related)

            suggestion.podcasts = related
            suggestion.save()

            # flag suggestions up-to-date
            p, _created = models.UserProfile.objects.get_or_create(user=user)
            p.suggestion_up_to_date = True
            p.save()

            progress(n+1, total)
