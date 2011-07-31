from django.core.management.base import BaseCommand

from mygpo import migrate
from mygpo.utils import iterate_together, progress
from mygpo.api import models as oldmodels
from mygpo.core import models as newmodels


class Command(BaseCommand):

    def handle(self, *args, **options):
        updated, deleted, created = 0, 0, 0
        key = lambda x: getattr(x, 'oldid', getattr(x, 'id'))

        oldgroups = oldmodels.PodcastGroup.objects.all().order_by('id')
        newgroups = newmodels.PodcastGroup.view('core/podcastgroups_by_oldid', include_docs=True).iterator()
        total = oldgroups.count()

        oldpodcasts = oldmodels.Podcast.objects.all().order_by('id')
        newpodcasts = newmodels.Podcast.view('core/podcasts_by_oldid').iterator()
        total += oldpodcasts.count()

        for n, (oldg, newg) in enumerate(iterate_together([oldgroups.iterator(), newgroups], key)):
            if (oldg != None) and (newg != None):
                updated += migrate.update_podcastgroup(oldg=oldg, newg=newg)

            elif oldg == None:
                deleted += 1
                newg.delete()

            elif newg == None:
                newg = migrate.create_podcastgroup(oldg)
                created += 1

            status_str = '%d new, %d upd, %d del' % (created, updated, deleted)
            progress(n, total, status_str)

        for n, (oldp, newp) in enumerate(iterate_together([oldpodcasts.iterator(), newpodcasts], key), n):

            if (oldp != None) and (newp != None):
                updated += migrate.update_podcast(oldp=oldp, newp=newp)

            elif oldp == None:
                deleted += 1
                newp.delete()

            elif newp == None:
                newp = migrate.create_podcast(oldp)
                created += 1

            status_str = '%d new, %d upd, %d del' % (created, updated, deleted)
            progress(n, total, status_str)
