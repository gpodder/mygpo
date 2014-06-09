from __future__ import unicode_literals

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes import generic

from uuidfield import UUIDField


class UUIDModel(models.Model):
    """ Models that have an UUID as primary key """

    id = UUIDField(primary_key=True)

    class Meta:
        abstract = True


class TitleModel(models.Model):
    """ Model that has a title """

    title = models.CharField(max_length=1000, null=False, blank=True,
                             db_index=True)
    subtitle = models.CharField(max_length=1000, null=False, blank=True)

    class Meta:
        abstract = True


class DescriptionModel(models.Model):
    """ Model that has a description """

    description = models.TextField(null=False, blank=True)

    class Meta:
        abstract = True


class LinkModel(models.Model):
    """ Model that has a link """

    link = models.URLField(null=True, max_length=1000)

    class Meta:
        abstract = True


class LanguageModel(models.Model):
    """ Model that has a language """

    language = models.CharField(max_length=10, null=True, blank=False)

    class Meta:
        abstract = True


class LastUpdateModel(models.Model):
    """ Model with timestamp of last update from its source """

    # date and time at which the model has last been updated from its source
    # (eg a podcast feed). None means that the object has been created as a
    # stub, without information from the source.
    last_update = models.DateTimeField(null=True)

    class Meta:
        abstract = True


class UpdateInfoModel(models.Model):

    # this does not use "auto_now_add=True" so that data
    # can be migrated with its creation timestamp intact; it can be
    # switched on after the migration is complete
    created = models.DateTimeField()
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class LicenseModel(models.Model):
    # URL to a license (usually Creative Commons)
    license = models.CharField(max_length=100, null=True, blank=False)

    class Meta:
        abstract = True


class FlattrModel(models.Model):
    # A Flattr payment URL
    flattr_url = models.URLField(null=True, blank=False, max_length=1000)

    class Meta:
        abstract = True


class ContentTypesModel(models.Model):
    # contains a comma-separated values of content types, eg 'audio,video'
    content_types = models.CharField(max_length=20, null=False, blank=True)

    class Meta:
        abstract = True


class MergedIdsModel(models.Model):

    class Meta:
        abstract = True


class OutdatedModel(models.Model):
    outdated = models.BooleanField(default=False)

    class Meta:
        abstract = True


class AuthorModel(models.Model):
    author = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        abstract = True


class UrlsMixin(models.Model):
    """ Methods for working with URL objects """

    urls = GenericRelation('URL', related_query_name='urls')

    class Meta:
        abstract = True


class SlugsMixin(models.Model):
    """ Methods for working with Slug objects """

    slugs = GenericRelation('Slug', related_query_name='slugs')

    class Meta:
        abstract = True

    @property
    def slug(self):
        """ The main slug of the podcast

        TODO: should be retrieved from a (materialized) view """
        slug = self.slugs.first()
        if slug is None:
            return None
        return slug.slug


class MergedUUIDsMixin(models.Model):
    """ Methods for working with MergedUUID objects """

    merged_uuids = GenericRelation('MergedUUID',
                                   related_query_name='merged_uuids')

    class Meta:
        abstract = True

class TagsMixin(models.Model):
    """ Methods for working with Tag objects """

    tags = GenericRelation('Tag', related_query_name='tags')

    class Meta:
        abstract = True


class OrderedModel(models.Model):
    """ A model that can be ordered

    The implementing Model must make sure that 'order' is sufficiently unique
    """

    order = models.PositiveSmallIntegerField()

    class Meta:
        abstract = True
        ordering = ['order']


class PodcastGroup(UUIDModel, TitleModel):
    """ Groups multiple podcasts together """


class PodcastQuerySet(models.QuerySet):
    """ Custom queries for Podcasts """

    def random(self):
        """ Random podcasts

        Excludes podcasts with missing title to guarantee some
        minimum quality of the results """
        return self.exclude(title='').order_by('?')


class Podcast(UUIDModel, TitleModel, DescriptionModel, LinkModel,
        LanguageModel, LastUpdateModel, UpdateInfoModel, LicenseModel,
        FlattrModel, ContentTypesModel, MergedIdsModel, OutdatedModel,
        AuthorModel, UrlsMixin, SlugsMixin, TagsMixin, MergedUUIDsMixin):
    """ A Podcast """

    logo_url = models.URLField(null=True, max_length=1000)
    group = models.ForeignKey(PodcastGroup, null=True)
    group_member_name = models.CharField(max_length=30, null=True, blank=False)

    # if p1 is related to p2, p2 is also related to p1
    related_podcasts = models.ManyToManyField('self', symmetrical=True)

    #subscribers = SchemaListProperty(SubscriberData)
    restrictions = models.CharField(max_length=20, null=True, blank=True)
    common_episode_title = models.CharField(max_length=50, null=False, blank=True)
    new_location = models.URLField(max_length=1000, null=True, blank=False)
    latest_episode_timestamp = models.DateTimeField(null=True)
    episode_count = models.PositiveIntegerField(default=0)
    hub = models.URLField(null=True)
    twitter = models.CharField(max_length=15, null=True, blank=False)

    objects = PodcastQuerySet.as_manager()

    def __str__(self):
        return self.title.encode('ascii', errors='replace')

    def __unicode(self):
        return self.title


class Episode(UUIDModel, TitleModel, DescriptionModel, LinkModel,
        LanguageModel, LastUpdateModel, UpdateInfoModel, LicenseModel,
        FlattrModel, ContentTypesModel, MergedIdsModel, OutdatedModel,
        AuthorModel, UrlsMixin, SlugsMixin, MergedUUIDsMixin):
    """ An episode """

    guid = models.CharField(max_length=50, null=True)
    content = models.TextField()
    released = models.DateTimeField(null=True)
    duration = models.PositiveIntegerField(null=True)
    filesize = models.BigIntegerField(null=True)
    mimetypes = models.CharField(max_length=50)
    podcast = models.ForeignKey(Podcast)
    listeners = models.PositiveIntegerField(null=True)

    class Meta:
        ordering = ['-released']

    def __str__(self):
        return self.title.encode('ascii', errors='replace')

    def __unicode__(self):
        return self.title


class ScopedModel(models.Model):

    # A slug / URL is unique within a scope; no two podcasts can have the same
    # URL (scope None), and no two episdoes of the same podcast (scope =
    # podcast-ID) can have the same URL
    scope = UUIDField(null=True)

    class Meta:
        abstract = True


class URL(OrderedModel, ScopedModel):
    """ Podcasts and Episodes can have multiple URLs

    URLs are ordered, and the first slug is considered the canonical one """

    url = models.URLField(max_length=2048)

    # see https://docs.djangoproject.com/en/1.6/ref/contrib/contenttypes/#generic-relations
    content_type = models.ForeignKey(ContentType)
    object_id = UUIDField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    class Meta:
        unique_together = (
            # a URL is unique per scope
            ('url', 'scope'),

            # URLs of an object must be ordered, so that no two slugs of one
            # object have the same order key
            ('content_type', 'object_id', 'order'),
        )

        verbose_name = 'URL'
        verbose_name_plural = 'URLs'


class Tag(models.Model):
    """ Tags any kind of Model

    See also :class:`TagsMixin`
    """

    FEED = 1
    DELICIOUS = 2
    USER = 4

    SOURCE_CHOICES = (
        (FEED, 'Feed'),
        (DELICIOUS, 'delicious'),
        (USER, 'User'),
    )

    tag = models.SlugField()
    source = models.PositiveSmallIntegerField(choices=SOURCE_CHOICES)
    #user = models.ForeignKey(null=True)

    # see https://docs.djangoproject.com/en/1.6/ref/contrib/contenttypes/#generic-relations
    content_type = models.ForeignKey(ContentType)
    object_id = UUIDField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    class Meta:
        unique_together = (
            # a tag can only be assigned once from one source to one item
            # TODO: add user to tuple
            ('tag', 'source', 'content_type', 'object_id'),
        )


class Slug(OrderedModel, ScopedModel):
    """ Slug for any kind of Model

    Slugs are ordered, and the first slug is considered the canonical one.
    See also :class:`SlugsMixin`
    """

    slug = models.SlugField(max_length=150)

    # see https://docs.djangoproject.com/en/1.6/ref/contrib/contenttypes/#generic-relations
    content_type = models.ForeignKey(ContentType)
    object_id = UUIDField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    class Meta:
        unique_together = (
            # a slug is unique per type; eg a podcast can have the same slug
            # as an episode, but no two podcasts can have the same slug
            ('slug', 'scope'),

            # slugs of an object must be ordered, so that no two slugs of one
            # object have the same order key
            ('content_type', 'object_id', 'order'),
        )

    def __repr__(self):
        return '{cls}(slug={slug}, order={order}, content_object={obj}'.format(
            cls=self.__class__.__name__,
            slug=self.slug,
            order=self.order,
            obj=self.content_object
        )


class MergedUUID(models.Model):
    """ If objects are merged their UUIDs are stored for later reference

    see also :class:`MergedUUIDsMixin`
    """

    uuid = UUIDField(unique=True)

    # see https://docs.djangoproject.com/en/1.6/ref/contrib/contenttypes/#generic-relations
    content_type = models.ForeignKey(ContentType)
    object_id = UUIDField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    class Meta:
        verbose_name = 'Merged UUID'
        verbose_name_plural = 'Merged UUIDs'
