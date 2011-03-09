from optparse import make_option

from couchdbkit import ResourceConflict
from django.core.management.base import BaseCommand

from mygpo.decorators import repeat_on_conflict
from mygpo.utils import progress, multi_request_view
from mygpo.core.models import Podcast, Episode


class Command(BaseCommand):
    """
    Moves Episodes that were previously in Podcasts into their own Documents

    During the migration to CouchDB, episodes have been included in their
    related Podcast documents. However this has proven to result in bad
    performance as the episodes are not always needed but would have to be
    loaded and parsed whenever the Podcast is accessed.

    This command is intended to be run twice in order to ensure a proper
    migration to stand-alone episodes. First it should be run without the
    --delete option so that Episodes documents are created for all existing
    episodes.

    Once that is done (and the rest of the application is updated to a version
    where it handles standalone Episodes) the command can be run again,
    this time with the --delete option, so that any outstanding episodes are
    migrated and all episodes are removed from their related podcasts,
    resulting in a performance gain.
    """


    option_list = BaseCommand.option_list + (
        make_option('--delete', action='store_true', dest='delete', default=False, help="Indicates if episodes in podcasts should be deleted."),
    )


    def handle(self, *args, **options):

        total = Podcast.view('core/podcasts_by_oldid', limit=0).total_rows
        podcasts = multi_request_view(Podcast, 'core/podcasts_by_id')

        for n, podcast in enumerate(podcasts):
            if not 'episodes' in podcast:
                continue

            for episode_id, episode in podcast.episodes.items():
                try:
                    e = Episode.get(episode_id)
                except:
                    episode._id = episode_id
                    try:
                        del episode.id
                    except AttributeError:
                        pass
                    episode.podcast = podcast.get_id()
                    episode.save()

                if options.get('delete', False):
                    del podcast.episodes[episode_id]

            if options.get('delete', False):
                self.remove_podcasts(podcast=podcast)

            progress(n+1, total)


    @repeat_on_conflict(['podcast'], reload_f=lambda x: Podcast.get(x.get_id()))
    def remove_podcasts(self, podcast):
        del podcast.episodes
        podcast.save()
