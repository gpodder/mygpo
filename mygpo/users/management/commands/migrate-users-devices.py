from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from mygpo import migrate
from mygpo.utils import progress
from mygpo.api.models import Device
from mygpo.users.models import PodcastUserState


class Command(BaseCommand):


    def handle(self, *args, **options):

        users = User.objects.all()

        if len(args) > 0:
            users = users.filter(username__in=args)

        total = users.count()

        for n, user in enumerate(users):
            devices = Device.objects.filter(user=user)
            for device in devices:

                # Creates Devices and updates it if it already exists
                migrate.save_device_signal(None, device)

            progress(n+1, total)
