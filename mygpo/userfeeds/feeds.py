from mygpo.api.models.users import EpisodeFavorite


class FavoriteFeed():

    def __init__(self, user):
        self.user = user

    def title(self):
        return '%s\'s Favorite Episodes' % self.user.username

    def get_episodes(self):
        return [x.episode for x in EpisodeFavorite.objects.filter(user=self.user).order_by('-created')]

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

