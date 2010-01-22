from django.core.management.base import BaseCommand
from mygpo.api.sanitizing import maintenance

class Command(BaseCommand):
    def handle(self, *args, **options):
        maintenance()

