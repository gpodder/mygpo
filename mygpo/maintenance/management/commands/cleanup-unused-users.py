from django.core.management.base import BaseCommand

from mygpo.users.models import User

from mygpo.utils import progress


class Command(BaseCommand):

    def handle(self, *args, **options):

        users = User.view('users/deleted',
                include_docs = True,
                reduce       = False,
            )

        total = User.view('users/deleted',
                reduce = True,
            )

        total = total['value'] if total else 0

        for n, user in enumerate(users):

            if user.is_active or not user.deleted:
                print 'skipping', user.username

            print 'deleting', user.username
            user.delete()

            progress(n+1, total)
