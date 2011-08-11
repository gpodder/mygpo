from itertools import count

from django.template.defaultfilters import slugify

from mygpo.core.models import Podcast, PodcastGroup, Episode


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



class PodcastSlug(SlugGenerator):
    """ Generates slugs for Podcasts """

    def _get_existing_slugs(self):
        db = Podcast.get_db()
        res = db.view('core/podcasts_by_slug',
                startkey = [self.base_slug, None],
                endkey   = [self.base_slug + 'ZZZZZ', None]
            )
        return [r['key'][0] for r in res]


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

        db = Episode.get_db()
        res = db.view('core/episodes_by_slug',
                startkey = [self.podcast_id, self.base_slug],
                endkey   = [self.podcast_id, self.base_slug + 'ZZZZZ']
            )
        return [r['key'][1] for r in res]


class ObjectsMissingSlugs(object):
    """ A collections of objects missing a slug """

    def __init__(self, cls, wrapper=None):
        self.db = cls.get_db()
        self.doc_type = cls._doc_type
        self.wrapper = wrapper

    def __len__(self):
        res = self.db.view('maintenance/missing_slugs',
                startkey     = [self.doc_type, {}],
                endkey       = [self.doc_type, None],
                descending   = True,
                reduce       = True,
                group        = True,
                group_level  = 1,
            )
        return res.first()['value']


    def __iter__(self):
        res = self.db.view('maintenance/missing_slugs',
                startkey     = [self.doc_type, {}],
                endkey       = [self.doc_type, None],
                descending   = True,
                include_docs = True,
                reduce       = False,
                wrapper      = self.wrapper,
            )
        return res.iterator()


class PodcastsMissingSlugs(ObjectsMissingSlugs):
    """ Podcasts that don't have a slug (but could have one) """

    def __init__(self):
        super(PodcastsMissingSlugs, self).__init__(Podcast, self._podcast_wrapper)

    @staticmethod
    def _podcast_wrapper(r):
        doc = r['doc']
        if doc['doc_type'] == 'Podcast':
            return Podcast.wrap(doc)
        else:
            pid = r['key'][2]
            pg = PodcastGroup.wrap(doc)
            return pg.get_podcast_by_id(pid)


class EpisodesMissingSlugs(ObjectsMissingSlugs):
    """ Episodes that don't have a slug (but could have one) """

    def __init__(self):
        super(EpisodesMissingSlugs, self).__init__(Episode, self._episode_wrapper)

    @staticmethod
    def _episode_wrapper(r):
        return Episode.wrap(r['doc'])
