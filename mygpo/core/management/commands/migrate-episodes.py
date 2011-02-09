from optparse import make_option

from django.core.management.base import BaseCommand

from mygpo import migrate
from mygpo.utils import iterate_together, progress
from mygpo.api import models as oldmodels
from mygpo.core import models as newmodels


class Command(BaseCommand):


    option_list = BaseCommand.option_list + (
        make_option('--min-id', action='store', type="int", dest='min_id', default=0, help="Id from which the migration should start."),
        make_option('--max-id', action='store', type="int", dest='max_id', help="Id at which the migration should end."),
    )

    def handle(self, *args, **options):

        min_id = options.get('min_id', 0)
        max_id = options.get('max_id', oldmodels.Episode.objects.order_by('-id')[0].id)

        updated, deleted, created = 0, 0, 0

        oldepisodes = oldmodels.Episode.objects.filter(id__gte=min_id, id__lte=max_id)
        newepisodes = newmodels.Episode.view('core/episodes_by_oldid', startkey=min_id, endkey=max_id).iterator()
        total = oldepisodes.count()
        compare = lambda o, n: cmp(long(o.id), long(n.oldid))

        for n, (olde, newe) in enumerate(iterate_together(oldepisodes, newepisodes, compare)):

            if (olde != None) and (newe != None):
                podcast = newmodels.Podcast.for_id(newe.podcast)
                updated += migrate.update_episode(olde, newe, podcast)

            elif olde == None:
                deleted += 1
                newe.delete()

            elif newe == None:
                newe = migrate.create_episode(olde)
                created += 1

            status_str = '%d new, %d upd, %d del' % (created, updated, deleted)
            progress(n, total, status_str)
