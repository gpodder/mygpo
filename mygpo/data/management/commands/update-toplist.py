from django.core.management.base import BaseCommand
from mygpo.api.models import Podcast, PodcastGroup, ToplistEntry, Subscription
from django.db.models import Count

class Command(BaseCommand):

    def handle(self, *args, **options):
        old_podcasts = {}
        old_groups = {}
        n=1
        for t in ToplistEntry.objects.all().only('subscriptions', 'podcast', 'podcast_group').order_by('-subscriptions'):
            if t.podcast:
                old_podcasts[t.podcast.id] = n
            else:
                old_groups[t.podcast_group.id] = n
            n += 1

        ToplistEntry.objects.all().delete()

        for p in Podcast.objects.filter(group=None):
            subscriptions = Subscription.objects.filter(podcast=p).values('user').distinct().count()
            ToplistEntry.objects.create(podcast=p, oldplace=old_podcasts.get(p.id, 0), subscriptions=subscriptions)

        for g in PodcastGroup.objects.all():
            subscriptions = Subscription.objects.filter(podcast__in=g.podcasts()).values('user').distinct().count()
            ToplistEntry.objects.create(podcast_group=g, oldplace=old_groups.get(g.id, 0), subscriptions=subscriptions)

