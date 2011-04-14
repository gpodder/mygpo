from itertools import count

from django.template.defaultfilters import slugify

from mygpo.core.models import Podcast, PodcastGroup


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


class PodcastsMissingSlugs(object):
    """ A collections of all podcasts missing a slug """

    def __init__(self):
        self.db = Podcast.get_db()

    def __len__(self):
        res = self.db.view('maintenance/missing_slugs',
                startkey     = ['Podcast', {}],
                endkey       = ['Podcast', None],
                descending   = True,
                reduce       = True,
                group        = True,
                group_level  = 1,
            )
        return res.first()['value']


    def __iter__(self):
        res = self.db.view('maintenance/missing_slugs',
                startkey     = ['Podcast', {}],
                endkey       = ['Podcast', None],
                descending   = True,
                include_docs = True,
                reduce       = False,
            )

        for r in res:
            doc = r['doc']
            if doc['doc_type'] == 'Podcast':
                yield Podcast.wrap(doc)
            else:
                pid = r['key'][2]
                pg = PodcastGroup.wrap(doc)
                yield pg.get_podcast_by_id(pid)
