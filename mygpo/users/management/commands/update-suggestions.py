from itertools import chain
from optparse import make_option
from operator import itemgetter
from collections import Counter

from django.core.management.base import BaseCommand

from mygpo.users.models import Suggestions, User
from mygpo.utils import progress
from mygpo.decorators import repeat_on_conflict
from mygpo.db.couchdb.user import suggestions_for_user


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--max', action='store', type='int', dest='max', default=15, help="Maximum number of suggested podcasts per user."),
        make_option('--max-users', action='store', type='int', dest='max_users', default=15, help="Maximum number of users to update."),
        make_option('--outdated-only', action='store_true', dest='outdated', default=False, help="Update only users where the suggestions are not up-to-date"),
        make_option('--user', action='store', type='string', dest='username', default='', help="Update a specific user"),
        )


    def handle(self, *args, **options):

        max_suggestions = options.get('max')

        if options.get('username'):
            users = [User.get_user(options.get('username'))]

        else:
            users = User.all_users()
            users = filter(lambda u: u.is_active, users)

            if options.get('outdated'):
                users = filter(lambda u: not u.suggestions_up_to_date, users)

        if options.get('max_users'):
            users = users[:int(options.get('max_users'))]

        total = len(users)

        for n, user in enumerate(users):
            suggestion = suggestions_for_user(user)

            subscribed_podcasts = list(set(user.get_subscribed_podcasts()))
            subscribed_podcasts = filter(None, subscribed_podcasts)

            subscribed_podcasts = filter(None, subscribed_podcasts)
            related = chain.from_iterable([p.related_podcasts for p in subscribed_podcasts])
            related = filter(lambda pid: not pid in suggestion.blacklist, related)

            counter = Counter(related)
            get_podcast_id = itemgetter(0)
            suggested = map(get_podcast_id, counter.most_common(max_suggestions))
            suggestion.podcasts = suggested

            suggestion.save()

            _update_user(user=user)

            progress(n+1, total)


@repeat_on_conflict(['user'])
def _update_user(user):
    user.suggestions_up_to_date = True
    user.save()
