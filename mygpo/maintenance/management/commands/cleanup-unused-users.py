from django.core.management.base import BaseCommand

from mygpo.users.models import User
from mygpo.utils import progress
from mygpo.db.couchdb.user import deleted_users, deleted_user_count


class Command(BaseCommand):

    def handle(self, *args, **options):

        users = deleted_users()
        total = deleted_user_count()

        for n, user in enumerate(users):

            if user.is_active or not user.deleted:
                print 'skipping', user.username

            print 'deleting', user.username,
            user.delete()

            progress(n+1, total)
