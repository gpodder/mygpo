import sys
import ConfigParser

from django.core.management.base import BaseCommand

from mygpo.decorators import repeat_on_conflict
from mygpo.core.models import SanitizingRule
from mygpo.utils import progress



class Command(BaseCommand):
    """
    """

    def handle(self, *args, **options):

        if not args:
            print >> sys.stderr, "Usage: ./manage.py delete-sanitizing-rules <slug> [<slug2> ...]"
            return


        for n, slug in enumerate(args):
            rule = SanitizingRule.for_slug(slug)

            if rule:
                self.delete_rule(rule=rule)

            progress(n+1, len(args))


    @repeat_on_conflict(['rule'])
    def delete_rule(self, rule):
        rule.delete()
