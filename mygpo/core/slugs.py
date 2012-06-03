from itertools import count

from couchdbkit.ext.django.schema import *

from django.template.defaultfilters import slugify

from mygpo.utils import multi_request_view
from mygpo.decorators import repeat_on_conflict


def assign_slug(obj, generator):
    if obj.slug:
        return

    slug = generator(obj).get_slug()
    _set_slug(obj=obj, slug=slug)


def assign_missing_episode_slugs(podcast):
    common_title = podcast.get_common_episode_title()

    episodes = EpisodesMissingSlugs(podcast.get_id())


    for episode in episodes:
        slug = EpisodeSlug(episode, common_title).get_slug()
        _set_slug(obj=episode, slug=slug)


@repeat_on_conflict(['obj'])
def _set_slug(obj, slug):
    if slug:
        obj.set_slug(slug)
        obj.save()



class SlugGenerator(object):
    """ Generates a unique slug for an object """


    def __init__(self, obj):
        if obj.slug:
            raise ValueError('%(obj)s already has slug %(slug)s' % \
                dict(obj=obj, slug=obj.slug))

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



class PodcastGroupSlug(SlugGenerator):
    """ Generates slugs for Podcast Groups """

    def _get_existing_slugs(self):
        from mygpo.core.models import Podcast

        db = Podcast.get_db()
        res = db.view('podcasts/by_slug',
                startkey = [self.base_slug, None],
                endkey   = [self.base_slug + 'ZZZZZ', None]
            )
        return [r['key'][0] for r in res]



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

    def __init__(self, episode, common_title):
        self.common_title = common_title
        super(EpisodeSlug, self).__init__(episode)
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


    def _get_existing_slugs(self):
        """ Episode slugs have to be unique within the Podcast """
        from mygpo.core.models import Episode

        db = Episode.get_db()
        res = db.view('episodes/by_slug',
                startkey = [self.podcast_id, self.base_slug],
                endkey   = [self.podcast_id, self.base_slug + 'ZZZZZ']
            )
        return [r['key'][1] for r in res]


class ObjectsMissingSlugs(object):
    """ A collections of objects missing a slug """

    def __init__(self, cls, wrapper=None, start=[None], end=[{}]):
        self.cls = cls
        self.doc_type = cls._doc_type
        self.wrapper = wrapper
        self.start = start
        self.end = end
        self.kwargs = {}

    def __len__(self):
        res = self.cls.view('slugs/missing',
                startkey     = [self.doc_type] + self.end,
                endkey       = [self.doc_type] + self.start,
                descending   = True,
                reduce       = True,
                group        = True,
                group_level  = 1,
            )
        return res.first()['value'] if res else 0


    def __iter__(self):

        return multi_request_view(self.cls, 'slugs/missing',
                startkey     = [self.doc_type] + self.end,
                endkey       = [self.doc_type] + self.start,
                descending   = True,
                include_docs = True,
                reduce       = False,
                wrapper      = self.wrapper,
                auto_advance = False,
                **self.kwargs
            )


class PodcastsMissingSlugs(ObjectsMissingSlugs):
    """ Podcasts that don't have a slug (but could have one) """

    def __init__(self):
        from mygpo.core.models import Podcast
        super(PodcastsMissingSlugs, self).__init__(Podcast, self._podcast_wrapper)
        self.kwargs = {'wrap': False}

    @staticmethod
    def _podcast_wrapper(r):
        from mygpo.core.models import Podcast, PodcastGroup

        doc = r['doc']

        if doc['doc_type'] == 'Podcast':
            return Podcast.wrap(doc)
        else:
            pid = r['key'][2]
            pg = PodcastGroup.wrap(doc)
            return pg.get_podcast_by_id(pid)

    def __iter__(self):
        for r in super(PodcastsMissingSlugs, self).__iter__():
            yield self._podcast_wrapper(r)


class EpisodesMissingSlugs(ObjectsMissingSlugs):
    """ Episodes that don't have a slug (but could have one) """

    def __init__(self, podcast_id=None):
        from mygpo.core.models import Episode

        if podcast_id:
            start = [podcast_id, None]
            end = [podcast_id, {}]
        else:
            start = [None, None]
            end = [{}, {}]

        super(EpisodesMissingSlugs, self).__init__(Episode,
                self._episode_wrapper, start, end)

    @staticmethod
    def _episode_wrapper(doc):
        from mygpo.core.models import Episode

        return Episode.wrap(doc)


class PodcastGroupsMissingSlugs(ObjectsMissingSlugs):
    """ Podcast Groups that don't have a slug (but could have one) """

    def __init__(self):
        from mygpo.core.models import PodcastGroup
        super(PodcastGroupsMissingSlugs, self).__init__(PodcastGroup,
            self._group_wrapper)

    @staticmethod
    def _group_wrapper(doc):
        from mygpo.core.models import PodcastGroup
        return PodcastGroup.wrap(doc)


class SlugMixin(DocumentSchema):
    slug         = StringProperty()
    merged_slugs = StringListProperty()

    def set_slug(self, slug):
        """ Set the main slug of the Podcast """

        if not isinstance(slug, basestring):
            raise ValueError('slug must be a string')

        if not slug:
            raise ValueError('slug cannot be empty')

        if self.slug:
            self.merged_slugs.append(self.slug)

        self.slug = slug
