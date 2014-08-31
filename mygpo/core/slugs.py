from itertools import count

from django.utils.text import slugify

from mygpo.podcasts.models import Slug, Episode


# TODO: move to feed-downloader?
def assign_missing_episode_slugs(podcast):
    common_title = podcast.get_common_episode_title()

    episodes = Episode.objects.filter(podcast=podcast, slugs__isnull=True)

    for episode in episodes:
        slug = EpisodeSlug(episode, common_title).get_slug()
        if slug:
            episode.set_slug(slug)


class SlugGenerator(object):
    """ Generates a unique slug for an object """


    def __init__(self, obj, override_existing=False):
        if obj.slug and not override_existing:
            raise ValueError('%(obj)s already has slug %(slug)s' % \
                dict(obj=obj, slug=obj.slug))

        self.obj = obj
        self.base_slug = self._get_base_slug(obj)


    @staticmethod
    def _get_base_slug(obj):
        if not obj.title:
            return None
        base_slug = slugify(obj.title)
        return base_slug


    @staticmethod
    def _get_existing_slugs():
        return []


    def get_slug(self):
        """ Gets existing slugs and appends numbers until slug is unique """
        if not self.base_slug:
            return None

        existing_slugs = self._get_existing_slugs()

        if not self.base_slug in existing_slugs:
            return str(self.base_slug)

        for n in count(1):
            tmp_slug = '%s-%d' % (self.base_slug, n)
            if not tmp_slug in existing_slugs:
                # slugify returns SafeUnicode, we need a plain string
                return str(tmp_slug)

    def _get_existing_slugs(self):
        query = Slug.objects.filter(scope=self.obj.scope,
                                    slug__startswith=self.base_slug)
        return [s.slug for s in query]


class PodcastGroupSlug(SlugGenerator):
    """ Generates slugs for Podcast Groups """

    pass


class PodcastSlug(PodcastGroupSlug):
    """ Generates slugs for Podcasts """

    @staticmethod
    def _get_base_slug(podcast):
        base_slug = SlugGenerator._get_base_slug(podcast)

        if not base_slug:
            return None

        # append group_member_name to slug
        if podcast.group_member_name:
            member_slug = slugify(podcast.group_member_name)
            if member_slug and not member_slug in base_slug:
                base_slug = '%s-%s' % (base_slug, member_slug)

        return base_slug



class EpisodeSlug(SlugGenerator):
    """ Generates slugs for Episodes """

    def __init__(self, episode, common_title, override_existing=False):
        self.common_title = common_title
        super(EpisodeSlug, self).__init__(episode, override_existing)
        self.podcast_id = episode.podcast


    def _get_base_slug(self, obj):

        number = obj.get_episode_number(self.common_title)
        if number:
            return str(number)

        short_title = obj.get_short_title(self.common_title)
        if short_title:
            return slugify(short_title)

        if obj.title:
            return slugify(obj.title)

        return None
