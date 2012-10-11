import sys
import ConfigParser

from django.core.management.base import BaseCommand

from mygpo.decorators import repeat_on_conflict
from mygpo.core.models import SanitizingRule
from mygpo.utils import progress
from mygpo.db.couchdb.common import sanitizingrule_for_slug



class Command(BaseCommand):
    """
    """

    def handle(self, *args, **options):

        if not args:
            print >> sys.stderr, "Usage: ./manage.py sync-sanitizing-rules <filename> [<filename2> ...]"
            return


        for filename in args:
            config = ConfigParser.ConfigParser()
            config.read(filename)
            sections = config.sections()

            for n, slug in enumerate(sections):
                rule = sanitizingrule_for_slug(slug) or SanitizingRule()

                self.update_rule(rule=rule, config=config, slug=slug)

                progress(n+1, len(sections), filename)


    @repeat_on_conflict(['rule'])
    def update_rule(self, rule, config, slug):
        rule.slug = slug
        rule.applies_to = []
        if config.getboolean(slug, 'podcast'):
            rule.applies_to.append('podcast')

        if config.getboolean(slug, 'episode'):
            rule.applies_to.append('episode')

        rule.search = config.get(slug, 'search')
        rule.replace = config.get(slug, 'replace')
        rule.priority = config.getint(slug, 'priority')
        rule.description = config.get(slug, 'description')
        rule.save()
