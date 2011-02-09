from django.core.management.base import BaseCommand

from mygpo import migrate
from mygpo.utils import iterate_together, progress
from mygpo.api import models as oldmodels
from mygpo.core import models as newmodels


class Command(BaseCommand):

    def handle(self, *args, **options):
        updated, deleted, created = 0, 0, 0
        max_id = oldmodels.Podcast.objects.all().order_by('-id')[0].id
        oldpodcasts = oldmodels.Podcast.objects.all().order_by('id').iterator()
        newpodcasts = newmodels.Podcast.view('core/podcasts_by_oldid').iterator()
        compare = lambda o, n: cmp(long(o.id), long(n.oldid))

        for oldp, newp in iterate_together(oldpodcasts, newpodcasts, compare):

            if (oldp != None) and (newp != None):
                updated += migrate.update_podcast(oldp=oldp, newp=newp)

            elif oldp == None:
                deleted += 1
                newp.delete()

            elif newp == None:
                newp = migrate.create_podcast(oldp)
                created += 1

            status_str = '%d new, %d upd, %d del' % (created, updated, deleted)
            progress(newp.oldid, max_id, status_str)
