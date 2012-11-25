from mygpo.cel import celery

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """ Django-enabled interface to the celery commandline tool """

    def handle(self, *args, **options):

        # Django gives only first argument to the command, celery expects
        # command name to be the first one, so we add a dummy element
        args = ('',) + args

        celery.start(args)
