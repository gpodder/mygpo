from django.core.management.base import BaseCommand
from optparse import make_option
from mygpo.api.models import Podcast, PodcastGroup
from mygpo.data.models import DirectoryEntry
from mygpo.data.directory import get_source_weights, get_weighted_tags, get_weighted_group_tags

class Command(BaseCommand):

    def handle(self, *args, **options):

        source_weights = get_source_weights()

        if len(args) > 0:
            podcasts = Podcast.objects.filter(url__in=args)

        else:
            podcasts = Podcast.objects.filter(group=None).order_by('id').only('id')

        for podcast in podcasts.iterator():

            print podcast.id
            DirectoryEntry.objects.filter(podcast=podcast).delete()

            for tag, weight in get_weighted_tags(podcast, source_weights).iteritems():
                if weight == 0:
                    continue

                DirectoryEntry.objects.create(podcast=podcast, tag=tag, ranking=weight)

        groups = PodcastGroup.objects.all().order_by('id').only('id')
        for group in groups.iterator():

            print group.id
            DirectoryEntry.objects.filter(podcast_group=group).delete()

            for tag, weight in get_weighted_group_tags(group, source_weights).iteritems():
                if weight == 0:
                    continue

                DirectoryEntry.objects.create(podcast_group=group, tag=tag, ranking=weight)

