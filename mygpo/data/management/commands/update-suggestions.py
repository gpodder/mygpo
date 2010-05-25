from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from optparse import make_option
from mygpo.api.models import Podcast, SuggestionEntry, Subscription
from mygpo.data.models import RelatedPodcast, SuggestionBlacklist
from mygpo.data.podcast import calc_similar_podcasts

class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--max', action='store', type='int', dest='max', default=15, help="Maximum number of suggested podcasts per user."),
        make_option('--outdated-only', action='store_true', dest='outdated', default=False, help="Update only users where the suggestions are not up-to-date"),
        make_option('--user', action='store', type='string', dest='username', default='', help="Update a specific user"),
        )

    def handle(self, *args, **options):

        max = options.get('max')

        users = User.objects.filter(is_active=True)

        if options.get('outdated'):
            users = users.filter(userprofile__suggestion_up_to_date=False)

        if options.get('username'):
            users = users.filter(username=options.get('username'))

        for user in users:
            subscribed_podcasts = set([s.podcast for s in Subscription.objects.filter(user=user)])
            related = RelatedPodcast.objects.filter(ref_podcast__in=subscribed_podcasts).exclude(rel_podcast__in=subscribed_podcasts)
            related_podcasts = {}
            for r in related:

                # remove potential suggestions that are in the same group as already subscribed podcasts
                if r.rel_podcast.group and Subscription.objects.filter(podcast__group=r.rel_podcast.group).exists():
                    continue

                # don't suggest blacklisted podcasts
                if SuggestionBlacklist.objects.filter(user=user, podcast=r.rel_podcast).exists():
                    continue

                related_podcasts[r.rel_podcast] = related_podcasts.get(r.rel_podcast, 0) + r.priority


            podcast_list = [(p, podcast) for (p, podcast) in related_podcasts.iteritems()]
            podcast_list.sort(key=lambda (p, priority): priority, reverse=True)

            SuggestionEntry.objects.filter(user=user).delete()
            for (p, priority) in podcast_list[:max]:
                SuggestionEntry.objects.create(podcast=p, priority=priority, user=user)


            p = user.get_profile()
            p.suggestion_up_to_date = True
            p.save()


