from django.core.management.base import BaseCommand
from mygpo.api.models import Device
from registration.models import RegistrationProfile

class Command(BaseCommand):

    def handle(self, *args, **options):

        for profile in RegistrationProfile.objects.all():

            if not profile.activation_key_expired():
                continue

            user = profile.user
            try:
                user_profile = user.get_profile()
                deleted = user_profile.deleted
            except:
                deleted = False

            if not user.is_active:
                if deleted:
                    continue

                devices = Device.objects.filter(user=user).count()
                print '%s (%s)' % (user, devices)

                if devices > 0:
                    user.is_active = True
                    profile.activation_key = RegistrationProfile.ACTIVATED
                    user.save()
                    profile.save()

                else:
                    profile.delete()
                    user.delete()

