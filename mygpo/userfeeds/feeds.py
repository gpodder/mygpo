from django.core.urlresolvers import reverse

from mygpo.podcasts.models import Episode
from mygpo.db.couchdb.episode_state import favorite_episode_ids_for_user



class FavoriteFeed():

    def __init__(self, user):
        self.user = user

    def title(self):
        return '%s\'s Favorite Episodes' % self.user.username

    def get_episodes(self):
        favorite_ids = favorite_episode_ids_for_user(self.user)
        return Episode.objects.get(id__in=favorite_ids)

    def language(self):
        """
        If all of the feed's episodes have the same language, return it,
        otherwise return an empty string
        """
        l = list(set([x.language for x in self.get_episodes() if x.language]))
        if len(l) == 1:
            return l[0]
        else:
            return ''

    def get_public_url(self, domain):
        return 'http://%s%s' % (domain, reverse('favorites-feed', args=[self.user.username]))
