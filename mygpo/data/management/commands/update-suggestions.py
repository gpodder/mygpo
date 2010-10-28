from optparse import make_option

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from mygpo.core.models import Podcast, Suggestions
from mygpo.api import models
from mygpo.data.models import RelatedPodcast
from mygpo.migrate import use_couchdb, create_podcast
from mygpo.utils import progress


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--max', action='store', type='int', dest='max', default=15, help="Maximum number of suggested podcasts per user."),
        make_option('--max-users', action='store', type='int', dest='max_users', default=15, help="Maximum number of users to update."),
        make_option('--outdated-only', action='store_true', dest='outdated', default=False, help="Update only users where the suggestions are not up-to-date"),
        make_option('--user', action='store', type='string', dest='username', default='', help="Update a specific user"),
        )


    @use_couchdb()
    def handle(self, *args, **options):

        max = options.get('max')

        users = User.objects.filter(is_active=True)

        if options.get('outdated'):
            users = users.filter(userprofile__suggestion_up_to_date=False)

        if options.get('username'):
            users = users.filter(username=options.get('username'))

        if options.get('max_users'):
            users = users[:int(options.get('max_users'))]

        total = users.count()

        for n, user in enumerate(users):
            suggestion = Suggestions.for_user_oldid(user.id)
            subscribed_podcasts = set([s.podcast for s in models.Subscription.objects.filter(user=user)])
            related = RelatedPodcast.objects.filter(ref_podcast__in=subscribed_podcasts).exclude(rel_podcast__in=subscribed_podcasts)
            related_podcasts = {}

            for r in related:

                # remove potential suggestions that are in the same group as already subscribed podcasts
                if r.rel_podcast.group and models.Subscription.objects.filter(podcast__group=r.rel_podcast.group).exists():
                    continue

                # don't suggest blacklisted podcasts
                p = Podcast.for_oldid(r.rel_podcast.id)
                if p._id in suggestion.blacklist:
                    continue

                related_podcasts[r.rel_podcast] = related_podcasts.get(r.rel_podcast, 0) + r.priority


            podcast_list = [(p, podcast) for (p, podcast) in related_podcasts.iteritems()]
            podcast_list.sort(key=lambda (p, priority): priority, reverse=True)

            ids = []
            for p, priority in podcast_list:
                newp = Podcast.for_oldid(p.id)
                if not newp:
                    newp = create_podcast(p)
                ids.append(newp._id)

            suggestion = Suggestions.for_user_oldid(user.id)
            suggestion.podcasts = ids
            suggestion.save()

            # flag suggestions up-to-date
            p, _created = models.UserProfile.objects.get_or_create(user=user)
            p.suggestion_up_to_date = True
            p.save()

            progress(n+1, total)
