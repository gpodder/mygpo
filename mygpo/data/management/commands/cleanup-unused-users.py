from django.core.management.base import BaseCommand
from mygpo.users.models import User

class Command(BaseCommand):

    def handle(self, *args, **options):

        for user in User.all_users():

            if not user.activation_key_expired():
                continue

            if not user.is_active and user.deleted:
                print 'deleting ', user
                #user.delete()
