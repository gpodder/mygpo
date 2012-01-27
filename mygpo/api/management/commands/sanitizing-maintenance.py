from optparse import make_option

from django.core.management.base import BaseCommand

from mygpo.api.sanitizing import maintenance


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--dry-run', action='store_true', dest='dry_run', default=False, help="Don't rewrite anything, just print the stats afterwards."),
        )


    def handle(self, *args, **options):

        maintenance(options.get('dry_run'))

