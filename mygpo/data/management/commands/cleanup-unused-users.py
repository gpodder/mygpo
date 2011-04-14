from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from mygpo.api.models import Device
from registration.models import RegistrationProfile

class Command(BaseCommand):

    def handle(self, *args, **options):

        for profile in RegistrationProfile.objects.all():

            if not profile.activation_key_expired():
                continue

            try:
                user = profile.user
            except User.DoesNotExist:
                profile.delete()

            try:
                user_profile = user.get_profile()
                deleted = user_profile.deleted
            except:
                deleted = False

            if not user.is_active and deleted:

                devices = Device.objects.filter(user=user)
                print '%s (%s)' % (user, devices.count())

                for device in devices:
                    device.delete()

                profile.delete()
                user_profile.delete()
                user.delete()
