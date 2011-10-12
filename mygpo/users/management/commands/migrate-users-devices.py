from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from mygpo import migrate
from mygpo.utils import progress
from mygpo.api.models import Device, SyncGroup
from mygpo.users.models import PodcastUserState
from mygpo.counter import Counter


class Command(BaseCommand):


    def handle(self, *args, **options):

        users = User.objects.all()

        if len(args) > 0:
            users = users.filter(username__in=args)

        total = users.count()

        for n, user in enumerate(users):

            actions = Counter()

            devices = Device.objects.filter(user=user)
            for device in devices:
                # Creates Devices and updates it if it already exists
                migrate.save_device_signal(None, device)
                actions['device'] += 1


            new_user = migrate.get_or_migrate_user(user)

            sync_groups = SyncGroup.objects.filter(user=user)
            for group in sync_groups:

                old_devices = group.devices()

                if len(old_devices) < 2:
                    continue

                devices = [new_user.get_device_by_uid(dev.uid) for dev
                            in old_devices]

                dev = devices[0]
                for other_dev in devices[1:]:
                    new_user.sync_devices(dev, other_dev)

                actions['group'] += 1
                new_user.save()


            progress(n+1, total, str(actions))
