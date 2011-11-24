from django.core.management.base import BaseCommand
from django.contrib.auth.models import User as OldUser

from mygpo import migrate
from mygpo.utils import progress
from mygpo.users.models import User


class Command(BaseCommand):


    def handle(self, *args, **options):

        users = OldUser.objects.all()

        if len(args) > 0:
            users = users.filter(username__in=args)

        total = users.count()

        for n, user in enumerate(users):

            u = User.for_oldid(user.id)
            migrate.update_user(u, user)

            try:
                u.save()
            except:
                print 'Error with user {oldid} - {newid}'.format(oldid=user.id,
                        newid=u._id)
                raise

            progress(n+1, total)
