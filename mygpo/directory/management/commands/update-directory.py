from django.core.management.base import BaseCommand
from mygpo.api.models import Podcast, PodcastGroup
from mygpo.data.models import DirectoryEntry

class Command(BaseCommand):

    def handle(self, *args, **options):

        if len(args) > 0:
            podcasts = Podcast.objects.filter(url__in=args)

        else:
            podcasts = Podcast.objects.filter(group=None).order_by('id').only('id')

        for podcast in podcasts.iterator():

            print podcast.id
            DirectoryEntry.objects.filter(podcast=podcast).delete()

            for tag in podcast.all_tags():
                DirectoryEntry.objects.create(podcast=podcast, tag=tag, ranking=1)

        groups = PodcastGroup.objects.all().order_by('id').only('id')
        for group in groups.iterator():

            print group.id
            DirectoryEntry.objects.filter(podcast_group=group).delete()

            for tag in group.all_tags():
                DirectoryEntry.objects.create(podcast_group=group, tag=tag, ranking=1)

