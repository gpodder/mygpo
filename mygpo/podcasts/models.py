from __future__ import unicode_literals

from datetime import datetime

from django.db import models, transaction
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes import generic

from uuidfield import UUIDField


# default podcast update interval in hours
DEFAULT_UPDATE_INTERVAL = 7 * 24

# minium podcast update interval in hours
MIN_UPDATE_INTERVAL = 5

# every podcast should be updated at least once a month
MAX_UPDATE_INTERVAL = 24 * 30


class UUIDModel(models.Model):
    """ Models that have an UUID as primary key """

    id = UUIDField(primary_key=True)

    class Meta:
        abstract = True

    def get_id(self):
        """ String representation of the ID """
        return self.id.hex


class TitleModel(models.Model):
    """ Model that has a title """

    title = models.CharField(max_length=1000, null=False, blank=True,
                             db_index=True)
    subtitle = models.TextField(null=False, blank=True)

    def __str__(self):
        return self.title.encode('ascii', errors='replace')

    def __unicode(self):
        return self.title

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

    language = models.CharField(max_length=10, null=True, blank=False,
                                db_index=True)

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
    created = models.DateTimeField(default=datetime.utcnow)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class LicenseModel(models.Model):
    # URL to a license (usually Creative Commons)
    license = models.CharField(max_length=100, null=True, blank=False,
                               db_index=True)

    class Meta:
        abstract = True


class FlattrModel(models.Model):
    # A Flattr payment URL
    flattr_url = models.URLField(null=True, blank=False, max_length=1000,
                                 db_index=True)

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
    outdated = models.BooleanField(default=False, db_index=True)

    class Meta:
        abstract = True


class AuthorModel(models.Model):
    author = models.CharField(max_length=350, null=True, blank=True)

    class Meta:
        abstract = True


class UrlsMixin(models.Model):
    """ Methods for working with URL objects """

    urls = GenericRelation('URL', related_query_name='urls')

    class Meta:
        abstract = True

    @property
    def url(self):
        """ The main URL of the model """
        url = self.urls.first()
        if url is None:
            return None
        return url.url


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


class PodcastGroup(UUIDModel, TitleModel, SlugsMixin):
    """ Groups multiple podcasts together """

    @property
    def scope(self):
        """ A podcast group is always in the global scope """
        return ''


class PodcastQuerySet(models.QuerySet):
    """ Custom queries for Podcasts """

    def random(self):
        """ Random podcasts

        Excludes podcasts with missing title to guarantee some
        minimum quality of the results """
        return self.exclude(title='').order_by('?')

    def flattr(self):
        """ Podcasts providing Flattr information """
        return self.exclude(flattr_url__isnull=True)

    def license(self, license_url=None):
        """ Podcasts with any / the given license """
        if license_url:
            return self.filter(license=license_url)
        else:
            return self.exclude(license__isnull=True)

    def order_by_next_update(self):
        """ Sort podcasts by next scheduled update """
        NEXTUPDATE = "last_update + (update_interval || ' hours')::INTERVAL"
        q = self.extra(select={'next_update': NEXTUPDATE})
        return q.order_by('next_update')

    @transaction.atomic
    def get_or_create_for_url(self, url):
        # TODO: where to specify how uuid is created?
        import uuid
        podcast, created = self.get_or_create(urls__url=url,
                                              defaults={
                                                'id': uuid.uuid1().hex,
                                              })

        if created:
            url = URL.objects.create(url=url,
                                     order=0,
                                     scope='',
                                     content_object=podcast,
                                    )
        return podcast

    def get_by_any_id(self, id):
        """ Find a Podcast by its own ID or by a merged ID """
        # TODO: should this be done in the model?
        try:
            return self.get(id=id)
        except self.model.DoesNotExist:
            return self.get(merged_uuids__uuid=id)


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
    restrictions = models.CharField(max_length=20, null=False, blank=True,
                                    default='')
    common_episode_title = models.CharField(max_length=100, null=False, blank=True)
    new_location = models.URLField(max_length=1000, null=True, blank=False)
    latest_episode_timestamp = models.DateTimeField(null=True)
    episode_count = models.PositiveIntegerField(default=0)
    hub = models.URLField(null=True)
    twitter = models.CharField(max_length=15, null=True, blank=False)
    update_interval = models.PositiveSmallIntegerField(null=False,
        default=DEFAULT_UPDATE_INTERVAL)

    objects = PodcastQuerySet.as_manager()

    def subscriber_count(self):
        # TODO: implement
        return 0

    def group_with(self, other, grouptitle, myname, othername):
        """ Group the podcast with another one """
        # TODO: move to PodcastGroup?

        if bool(self.group) and (self.group == other.group):
            # they are already grouped
            return

        group1 = self.group
        group2 = other.group

        if group1 and group2:
            raise ValueError('both podcasts already are in different groups')

        elif not (group1 or group2):
            # Form a new group
            import uuid
            group = PodcastGroup.objects.create(id=uuid.uuid1(), title=grouptitle)
            self.group_member_name = myname
            self.group = group
            self.save()

            other.group_member_name = othername
            other.group = group
            other.save()

            return group

        elif group1:
            # add other to self's group
            other.group_member_name = othername
            other.group = group1
            other.save()
            return group1

        else:
            # add self to other's group
            self.group_member_name = myname
            self.group = group2
            self.save()
            return group2


    def subscribe_targets(self, user):
        """
        returns all Devices and SyncGroups on which this podcast can be subsrbied. This excludes all
        devices/syncgroups on which the podcast is already subscribed
        """
        targets = []

        subscriptions_by_devices = user.get_subscriptions_by_device()

        for group in user.get_grouped_devices():

            if group.is_synced:

                dev = group.devices[0]

                if not self.get_id() in subscriptions_by_devices[dev.id]:
                    targets.append(group.devices)

            else:
                for device in group.devices:
                    if not self.get_id() in subscriptions_by_devices[device.id]:
                        targets.append(device)

        return targets


    def get_common_episode_title(self, num_episodes=100):

        if self.common_episode_title:
            return self.common_episode_title

        episodes = self.episode_set.all()[:num_episodes]

        # We take all non-empty titles
        titles = filter(None, (e.title for e in episodes))

        # there can not be a "common" title of a single title
        if len(titles) < 2:
            return None

        # get the longest common substring
        common_title = utils.longest_substr(titles)

        # but consider only the part up to the first number. Otherwise we risk
        # removing part of the number (eg if a feed contains episodes 100-199)
        common_title = re.search(r'^\D*', common_title).group(0)

        if len(common_title.strip()) < 2:
            return None

        return common_title

    @property
    def scope(self):
        """ A podcast is always in the global scope """
        return ''


class Episode(UUIDModel, TitleModel, DescriptionModel, LinkModel,
        LanguageModel, LastUpdateModel, UpdateInfoModel, LicenseModel,
        FlattrModel, ContentTypesModel, MergedIdsModel, OutdatedModel,
        AuthorModel, UrlsMixin, SlugsMixin, MergedUUIDsMixin):
    """ An episode """

    guid = models.CharField(max_length=200, null=True)
    content = models.TextField()
    released = models.DateTimeField(null=True)
    duration = models.PositiveIntegerField(null=True)
    filesize = models.BigIntegerField(null=True)
    mimetypes = models.CharField(max_length=100)
    podcast = models.ForeignKey(Podcast)
    listeners = models.PositiveIntegerField(null=True)

    class Meta:
        ordering = ['-released']

    @property
    def scope(self):
        """ An episode's scope is its podcast """
        return self.podcast_id.hex

    def get_short_title(self, common_title):
        """ Title when used within the podcast's context """
        if not self.title or not common_title:
            return None

        title = self.title.replace(common_title, '').strip()
        title = re.sub(r'^[\W\d]+', '', title)
        return title


    def get_episode_number(self, common_title):
        """ Number of the episode """
        if not self.title or not common_title:
            return None

        title = self.title.replace(common_title, '').strip()
        match = re.search(r'^\W*(\d+)', title)
        if not match:
            return None

        return int(match.group(1))


class ScopedModel(models.Model):
    """ A model that belongs to some scope, usually for limited uniqueness

    scope does not allow null values, because null is not equal to null in SQL.
    It could therefore not be used in unique constraints. """

    # A slug / URL is unique within a scope; no two podcasts can have the same
    # URL (scope ''), and no two episdoes of the same podcast (scope =
    # podcast-ID) can have the same URL
    scope = models.CharField(max_length=32, null=False, blank=True,
                             db_index=True)

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

    slug = models.SlugField(max_length=150, db_index=True)

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
