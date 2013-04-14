import sys
from optparse import make_option

from django.core.management.base import BaseCommand

from mygpo.maintenance import merge

class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--dry-run',        action='store_true', dest='dry_run',        default=False, help="Perform a dry-run without actually changing anything"),
        make_option('--podcasts',       action='store_true', dest='podcasts',       default=False, help="Perform merging for Podcasts "),
        make_option('--podcast-states', action='store_true', dest='podcast_states', default=False, help="Perform merging for Podcast states"),
        make_option('--episodes',       action='store_true', dest='episodes',       default=False, help="Perform merging for Episodes"),
        make_option('--episode_states', action='store_true', dest='episode_states', default=False, help="Perform merging for Episode states"),
        make_option('--all',            action='store_true', dest='all',            default=False, help="Perform all merges"),
    )

    def handle(self, *args, **options):

        dry_run        = options.get('dry_run') or options.get('all')
        podcasts       = options.get('podcasts') or options.get('all')
        podcast_states = options.get('podcast_states') or options.get('all')
        episodes       = options.get('episodes') or options.get('all')
        episode_states = options.get('episode_states') or options.get('all')

        if not any([podcasts, podcast_states, episodes, episode_states]):
            print >> sys.stderr, 'Usage: ./manage.py merge-duplicates [--dry-run] ( --podcasts | --podcast-states | --episodes | --episode-states )+'
            return

        merge.merge_objects(podcasts=podcasts, podcast_states=podcast_states,
                episodes=episodes, episode_states=episode_states, dry_run=dry_run)
