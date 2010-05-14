from django.core.management.base import BaseCommand
from optparse import make_option
from mygpo.api.models import Podcast, PodcastGroup, ToplistEntry, Subscription, SubscriptionMeta
from django.db.models import Count

class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--preserve-oldplace', action='store_true', dest='preserve_oldplace', default=False, help="Indicates that the Last (week's) position should not be updated."),
    )


    def handle(self, *args, **options):
        old_podcasts = {}
        old_groups = {}
        n=1
        for t in ToplistEntry.objects.all().only('subscriptions', 'podcast', 'podcast_group').order_by('-subscriptions'):

            if options.get('preserve_oldplace'):
                oldplace = t.oldplace
            else:
                oldplace = n

            if t.podcast:
                old_podcasts[t.podcast.id] = oldplace
            else:
                old_groups[t.podcast_group.id] = oldplace
            n += 1

        ToplistEntry.objects.all().delete()

        for p in Podcast.objects.filter(group=None).order_by('id'):
            subscription_count = p.subscriber_count()
            ToplistEntry.objects.create(podcast=p, oldplace=old_podcasts.get(p.id, 0), subscriptions=subscription_count)

        for g in PodcastGroup.objects.all().order_by('id'):
            total = 0
            for p in g.podcasts():
                total += p.subscriber_count()

            ToplistEntry.objects.create(podcast_group=g, oldplace=old_groups.get(g.id, 0), subscriptions=total)

