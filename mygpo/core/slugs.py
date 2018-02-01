from itertools import count

from django.utils.text import slugify


class SlugGenerator(object):
    """ Generates a unique slug for an object """

    def __init__(self, obj):
        self.obj = obj
        self.base_slug = self._get_base_slug(obj)

    @staticmethod
    def _get_base_slug(obj):
        if not obj.title:
            return None
        base_slug = slugify(obj.title)
        return base_slug

    def __iter__(self):
        """ Generates possible slugs

        The consumer can can consume until it get's an unused one """

        if self.obj.slug:
            # The object already has a slug
            raise StopIteration

        if not self.base_slug:
            raise StopIteration

        # first we try with the base slug
        yield str(self.base_slug)

        for n in count(1):
            tmp_slug = '%s-%d' % (self.base_slug, n)
            # slugify returns SafeUnicode, we need a plain string
            yield str(tmp_slug)


class PodcastGroupSlugs(SlugGenerator):
    """ Generates slugs for Podcast Groups """
    pass


class PodcastSlugs(PodcastGroupSlugs):
    """ Generates slugs for Podcasts """

    def _get_base_slug(self, podcast):
        base_slug = SlugGenerator._get_base_slug(podcast)

        if not base_slug:
            return None

        # append group_member_name to slug
        if podcast.group_member_name:
            member_slug = slugify(podcast.group_member_name)
            if member_slug and not member_slug in base_slug:
                base_slug = '%s-%s' % (base_slug, member_slug)

        return base_slug


class EpisodeSlugs(SlugGenerator):
    """ Generates slugs for Episodes """

    def __init__(self, episode, common_title):
        self.common_title = common_title
        super().__init__(episode)

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
