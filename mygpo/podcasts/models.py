import collections
import uuid
import re
from datetime import timedelta

from django.core.cache import cache
from django.conf import settings
from django.db import models, transaction, IntegrityError, DataError
from django.db.models import F
from django.utils.translation import gettext as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation, GenericForeignKey
from django.contrib.postgres.search import SearchVectorField

from mygpo import utils
from mygpo.core.models import (
    TwitterModel,
    UUIDModel,
    GenericManager,
    UpdateInfoModel,
    OrderedModel,
    OptionallyOrderedModel,
)

import logging

logger = logging.getLogger(__name__)


GetCreateResult = collections.namedtuple("GetCreateResult", "object created")


# default podcast update interval in hours
DEFAULT_UPDATE_INTERVAL = 7 * 24

# minium podcast update interval in hours
MIN_UPDATE_INTERVAL = 5

# every podcast should be updated at least once a month
MAX_UPDATE_INTERVAL = 24 * 30


class TitleModel(models.Model):
    """ Model that has a title """

    title = models.CharField(max_length=1000, null=False, blank=True, db_index=True)
    subtitle = models.TextField(null=False, blank=True)

    def __str__(self):
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

    language = models.CharField(max_length=10, null=True, blank=True, db_index=True)

    class Meta:
        abstract = True


class LastUpdateModel(models.Model):
    """ Model with timestamp of last update from its source """

    # date and time at which the model has last been updated from its source
    # (eg a podcast feed). None means that the object has been created as a
    # stub, without information from the source.
    last_update = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True


class LicenseModel(models.Model):
    # URL to a license (usually Creative Commons)
    license = models.CharField(max_length=100, null=True, blank=True, db_index=True)

    class Meta:
        abstract = True


class FlattrModel(models.Model):
    # A Flattr payment URL
    flattr_url = models.URLField(null=True, blank=True, max_length=1000, db_index=True)

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


class MergedUUIDQuerySet(models.QuerySet):
    """ QuerySet for Models inheriting from MergedUUID """

    def get_by_any_id(self, id):
        """ Find am Episode by its own ID or by a merged ID """
        # TODO: should this be done in the model?
        try:
            return self.get(id=id)
        except self.model.DoesNotExist:
            return self.get(merged_uuids__uuid=id)


class TagsMixin(models.Model):
    """ Methods for working with Tag objects """

    tags = GenericRelation("Tag", related_query_name="tags")

    class Meta:
        abstract = True


class ScopedModel(models.Model):
    """A model that belongs to some scope, usually for limited uniqueness

    scope does not allow null values, because null is not equal to null in SQL.
    It could therefore not be used in unique constraints."""

    # A slug / URL is unique within a scope; no two podcasts can have the same
    # URL (scope ''), and no two episdoes of the same podcast (scope =
    # podcast-ID) can have the same URL
    scope = models.CharField(max_length=32, null=False, blank=True, db_index=True)

    class Meta:
        abstract = True

    def get_default_scope(self):
        """ Returns the default scope of the object """
        raise NotImplementedError(
            "{cls} should implement get_default_scope".format(
                cls=self.__class__.__name__
            )
        )


class Slug(OrderedModel, ScopedModel):
    """Slug for any kind of Model

    Slugs are ordered, and the first slug is considered the canonical one.
    See also :class:`SlugsMixin`
    """

    slug = models.SlugField(max_length=150, db_index=True)

    # see https://docs.djangoproject.com/en/1.6/ref/contrib/contenttypes/#generic-relations
    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.UUIDField()
    content_object = GenericForeignKey("content_type", "object_id")

    class Meta(OrderedModel.Meta):
        unique_together = (
            # a slug is unique per type; eg a podcast can have the same slug
            # as an episode, but no two podcasts can have the same slug
            ("slug", "scope"),
            # slugs of an object must be ordered, so that no two slugs of one
            # object have the same order key
            ("content_type", "object_id", "order"),
        )

        index_together = [("slug", "content_type")]

    def __repr__(self):
        return "{cls}(slug={slug}, order={order}, content_object={obj}".format(
            cls=self.__class__.__name__,
            slug=self.slug,
            order=self.order,
            obj=self.content_object,
        )


class SlugsMixin(models.Model):
    """ Methods for working with Slug objects """

    slugs = GenericRelation(Slug, related_query_name="slugs")

    class Meta:
        abstract = True

    @property
    def slug(self):
        """The main slug of the podcast

        TODO: should be retrieved from a (materialized) view"""

        # We could also use self.slugs.first() here, but this would result in a
        # different query and would render a .prefetch_related('slugs') useless
        # The assumption is that we will never have loads of slugs, so
        # fetching all won't hurt
        slugs = list(self.slugs.all())
        slug = slugs[0].slug if slugs else None
        logger.debug("Found slugs %r, picking %r", slugs, slug)
        return slug

    def add_slug(self, slug):
        """ Adds a (non-cannonical) slug """

        if not slug:
            raise ValueError("'%s' is not a valid slug" % slug)

        existing_slugs = self.slugs.all()

        # cut slug to the maximum allowed length
        slug = utils.to_maxlength(Slug, "slug", slug)

        # check if slug already exists
        if slug in [s.slug for s in existing_slugs]:
            return

        max_order = max([-1] + [s.order for s in existing_slugs])
        next_order = max_order + 1
        Slug.objects.create(
            scope=self.scope, slug=slug, content_object=self, order=next_order
        )

    def set_slug(self, slug):
        """ Sets the canonical slug """

        slugs = [s.slug for s in self.slugs.all()]
        if slug in slugs:
            slugs.remove(slug)

        slugs.insert(0, slug)
        self.set_slugs(slugs)

    def remove_slug(self, slug):
        """ Removes a slug """
        Slug.objects.filter(
            slug=slug,
            content_type=ContentType.objects.get_for_model(self),
            object_id=self.id,
        ).delete()

    def set_slugs(self, slugs):
        """Update the object's slugs to the given list

        'slugs' should be a list of strings. Slugs that do not exist are
        created.  Existing slugs that are not in the 'slugs' list are
        deleted."""
        slugs = [utils.to_maxlength(Slug, "slug", slug) for slug in slugs]
        existing = {s.slug: s for s in self.slugs.all()}
        utils.set_ordered_entries(self, slugs, existing, Slug, "slug", "content_object")


class PodcastGroup(UUIDModel, TitleModel, SlugsMixin):
    """ Groups multiple podcasts together """

    @property
    def scope(self):
        """ A podcast group is always in the global scope """
        return ""

    def subscriber_count(self):
        # this could be done directly in the DB
        return sum([p.subscriber_count() for p in self.podcast_set.all()] + [0])

    @property
    def logo_url(self):
        podcast = self.podcast_set.first()
        podcast.logo_url


class PodcastQuerySet(MergedUUIDQuerySet):
    """ Custom queries for Podcasts """

    def random(self):
        """Random podcasts

        Excludes podcasts with missing title to guarantee some
        minimum quality of the results"""

        # Using PostgreSQL's RANDOM() is very expensive, so we're generating a
        # random uuid and query podcasts with a higher ID
        # This returns podcasts in order of their ID, but the assumption is
        # that usually only one podcast will be required anyway
        import uuid

        ruuid = uuid.uuid1()
        return self.exclude(title="").filter(id__gt=ruuid)

    def license(self, license_url=None):
        """ Podcasts with any / the given license """
        if license_url:
            return self.filter(license=license_url)
        else:
            return self.exclude(license__isnull=True)

    def order_by_next_update(self):
        """ Sort podcasts by next scheduled update """
        NEXTUPDATE = (
            "last_update + (update_interval * "
            "update_interval_factor || ' hours')::INTERVAL"
        )
        q = self.extra(select={"_next_update": NEXTUPDATE})
        return q.order_by("_next_update")

    @property
    def next_update(self):
        interval = timedelta(hours=self.update_interval) * self.update_interval_factor
        return self.last_update + interval

    def next_update_between(self, start, end):
        NEXTUPDATE_BETWEEN = (
            "(last_update + (update_interval * "
            " update_interval_factor || "
            "' hours')::INTERVAL) BETWEEN %s AND %s"
        )
        return self.extra(where=[NEXTUPDATE_BETWEEN], params=[start, end])

    def toplist(self, language=None):
        toplist = self
        if language:
            toplist = toplist.filter(language=language)

        return toplist.order_by("-subscribers")


class PodcastManager(GenericManager):
    """ Manager for the Podcast model """

    def get_queryset(self):
        return PodcastQuerySet(self.model, using=self._db)

    def get_advertised_podcast(self):
        """ Returns the currently advertised podcast """
        if settings.PODCAST_AD_ID:
            podcast = cache.get("podcast_ad")
            if podcast:
                return podcast

            pk = uuid.UUID(settings.PODCAST_AD_ID)
            podcast = self.get_queryset().get(pk=pk)
            cache.set("pocdast_ad", podcast)
            return podcast

    @transaction.atomic
    def get_or_create_for_url(self, url, defaults={}):

        if not url:
            raise ValueError("The URL must not be empty")

        # TODO: where to specify how uuid is created?
        import uuid

        defaults.update({"id": uuid.uuid1()})

        url = utils.to_maxlength(URL, "url", url)
        try:
            # try to fetch the podcast
            podcast = Podcast.objects.get(urls__url=url, urls__scope="")
            return GetCreateResult(podcast, False)

        except Podcast.DoesNotExist:
            # episode did not exist, try to create it
            try:
                with transaction.atomic():
                    podcast = Podcast.objects.create(**defaults)
                    url = URL.objects.create(
                        url=url, order=0, scope="", content_object=podcast
                    )
                    return GetCreateResult(podcast, True)

            # URL could not be created, so it was created since the first get
            except IntegrityError:
                podcast = Podcast.objects.get(urls__url=url, urls__scope="")
                return GetCreateResult(podcast, False)


class URL(OrderedModel, ScopedModel):
    """Podcasts and Episodes can have multiple URLs

    URLs are ordered, and the first slug is considered the canonical one"""

    url = models.URLField(max_length=2048)

    # see https://docs.djangoproject.com/en/1.6/ref/contrib/contenttypes/#generic-relations
    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.UUIDField()
    content_object = GenericForeignKey("content_type", "object_id")

    class Meta(OrderedModel.Meta):
        unique_together = (
            # a URL is unique per scope
            ("url", "scope"),
            # URLs of an object must be ordered, so that no two slugs of one
            # object have the same order key
            ("content_type", "object_id", "order"),
        )

        verbose_name = "URL"
        verbose_name_plural = "URLs"

    def get_default_scope(self):
        return self.content_object.scope


class UrlsMixin(models.Model):
    """ Methods for working with URL objects """

    urls = GenericRelation(URL, related_query_name="urls")

    class Meta:
        abstract = True

    @property
    def url(self):
        """ The main URL of the model """
        # We could also use self.urls.first() here, but this would result in a
        # different query and would render a .prefetch_related('urls') useless
        # The assumption is that we will never have loads of URLS, so
        # fetching all won't hurt
        urls = list(self.urls.all())
        return urls[0].url if urls else None

    def add_missing_urls(self, new_urls):
        """Adds missing URLS from new_urls

        The order of existing URLs is not changed"""
        existing_urls = self.urls.all()
        next_order = max([-1] + [u.order for u in existing_urls]) + 1
        existing_urls = [u.url for u in existing_urls]

        for url in new_urls:
            if url in existing_urls:
                continue

            try:
                URL.objects.create(
                    url=url, order=next_order, scope=self.scope, content_object=self
                )
                next_order += 1
            except (IntegrityError, DataError) as ie:
                err = str(ie)
                logger.warning(u"Could not add URL: {0}".format(err))
                continue

    def set_url(self, url):
        """ Sets the canonical URL """

        urls = [u.url for u in self.urls.all()]
        if url in urls:
            urls.remove(url)

        urls.insert(0, url)
        self.set_urls(urls)

    def set_urls(self, urls):
        """Update the object's URLS to the given list

        'urls' should be a list of strings. Slugs that do not exist are
        created.  Existing urls that are not in the 'urls' list are
        deleted."""
        urls = [utils.to_maxlength(URL, "url", url) for url in urls]
        existing = {u.url: u for u in self.urls.all()}
        utils.set_ordered_entries(self, urls, existing, URL, "url", "content_object")


class MergedUUID(models.Model):
    """If objects are merged their UUIDs are stored for later reference

    see also :class:`MergedUUIDsMixin`
    """

    uuid = models.UUIDField(unique=True)

    # see https://docs.djangoproject.com/en/1.6/ref/contrib/contenttypes/#generic-relations
    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.UUIDField()
    content_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        verbose_name = "Merged UUID"
        verbose_name_plural = "Merged UUIDs"


class MergedUUIDsMixin(models.Model):
    """ Methods for working with MergedUUID objects """

    merged_uuids = GenericRelation(MergedUUID, related_query_name="merged_uuids")

    class Meta:
        abstract = True


class Podcast(
    UUIDModel,
    TitleModel,
    DescriptionModel,
    LinkModel,
    LanguageModel,
    LastUpdateModel,
    UpdateInfoModel,
    LicenseModel,
    FlattrModel,
    ContentTypesModel,
    MergedIdsModel,
    OutdatedModel,
    AuthorModel,
    UrlsMixin,
    SlugsMixin,
    TagsMixin,
    MergedUUIDsMixin,
    TwitterModel,
):
    """ A Podcast """

    logo_url = models.URLField(null=True, max_length=1000)
    group = models.ForeignKey(
        PodcastGroup, null=True, blank=True, on_delete=models.PROTECT
    )
    group_member_name = models.CharField(max_length=30, null=True, blank=True)

    # if p1 is related to p2, p2 is also related to p1
    related_podcasts = models.ManyToManyField("self", symmetrical=True, blank=True)

    subscribers = models.PositiveIntegerField(default=0)
    restrictions = models.CharField(max_length=20, null=False, blank=True, default="")
    common_episode_title = models.CharField(max_length=100, null=False, blank=True)
    new_location = models.URLField(max_length=1000, null=True, blank=True)
    latest_episode_timestamp = models.DateTimeField(null=True, blank=True)
    episode_count = models.PositiveIntegerField(default=0, blank=True)
    hub = models.URLField(null=True, blank=True)

    # Interval between episodes, within a specified range
    update_interval = models.PositiveSmallIntegerField(
        null=False, default=DEFAULT_UPDATE_INTERVAL
    )

    # factor to increase update_interval if an update does not find any
    # new episodes
    update_interval_factor = models.FloatField(default=1)

    # "order" value of the most recent episode (will be the highest of all)
    max_episode_order = models.PositiveIntegerField(null=True, blank=True, default=None)

    # indicates whether the search index is up-to-date (or needs updating)
    search_index_uptodate = models.BooleanField(default=False, db_index=True)

    # search vector for full-text search
    search_vector = SearchVectorField(null=True)

    objects = PodcastManager()

    class Meta:
        index_together = [("last_update",)]

    def subscriber_count(self):
        # TODO: implement
        return self.subscribers

    def group_with(self, other, grouptitle, myname, othername):
        """ Group the podcast with another one """
        # TODO: move to PodcastGroup?

        if bool(self.group) and (self.group == other.group):
            # they are already grouped
            return

        group1 = self.group
        group2 = other.group

        if group1 and group2:
            raise ValueError("both podcasts already are in different groups")

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

    def get_common_episode_title(self, num_episodes=100):

        if self.common_episode_title:
            return self.common_episode_title

        episodes = self.episode_set.all()[:num_episodes]

        # We take all non-empty titles
        titles = [_f for _f in (e.title for e in episodes) if _f]

        # there can not be a "common" title of a single title
        if len(titles) < 2:
            return None

        # get the longest common substring
        common_title = utils.longest_substr(titles)

        # but consider only the part up to the first number. Otherwise we risk
        # removing part of the number (eg if a feed contains episodes 100-199)
        common_title = re.search(r"^\D*", common_title).group(0)

        if len(common_title.strip()) < 2:
            return None

        return common_title

    def get_episode_before(self, episode):
        if not episode.released:
            return None
        return self.episode_set.filter(released__lt=episode.released).latest()

    def get_episode_after(self, episode):
        if not episode.released:
            return None
        return self.episode_set.filter(released__gt=episode.released).first()

    @property
    def scope(self):
        """ A podcast is always in the global scope """
        return ""

    @property
    def as_scope(self):
        """ If models use this object as scope, they'll use this value """
        return self.id.hex

    @property
    def display_title(self):
        """ a title for display purposes """
        if self.title:
            return self.title

        if not self.url:
            logger.warning(
                "Podcast with ID {podcast_id} does not have a URL".format(
                    podcast_id=self.id
                )
            )
            return _("Unknown Podcast")

        return _(
            "Unknown Podcast from {domain}".format(domain=utils.get_domain(self.url))
        )

    @property
    def next_update(self):
        if not self.last_update:
            return None

        interval = timedelta(hours=self.update_interval) * self.update_interval_factor
        return self.last_update + interval


class EpisodeQuerySet(MergedUUIDQuerySet):
    """ QuerySet for Episodes """

    def toplist(self, language=None):
        toplist = self
        if language:
            toplist = toplist.filter(language=language)

        return toplist.order_by("-listeners")


class EpisodeManager(GenericManager):
    """ Custom queries for Episodes """

    def get_queryset(self):
        return EpisodeQuerySet(self.model, using=self._db)

    def get_or_create_for_url(self, podcast, url, defaults={}):
        """Create an Episode for a given URL

        This is the only place where new episodes are created"""

        if not url:
            raise ValueError("The URL must not be empty")

        # TODO: where to specify how uuid is created?
        import uuid

        url = utils.to_maxlength(URL, "url", url)

        try:
            url = URL.objects.get(url=url, scope=podcast.as_scope)
            created = False
            episode = url.content_object

            if episode is None:

                with transaction.atomic():
                    episode = Episode.objects.create(
                        podcast=podcast, id=uuid.uuid1(), **defaults
                    )

                    url.content_object = episode
                    url.save()
                    created = True

            return GetCreateResult(episode, created)

        except URL.DoesNotExist:
            # episode did not exist, try to create it
            try:
                with transaction.atomic():
                    episode = Episode.objects.create(
                        podcast=podcast, id=uuid.uuid1(), **defaults
                    )

                    url = URL.objects.create(
                        url=url, order=0, scope=episode.scope, content_object=episode
                    )

                    # Keep episode_count up to date here; it is not
                    # recalculated when updating the podcast because counting
                    # episodes can be very slow for podcasts with many episodes
                    Podcast.objects.filter(pk=podcast.pk).update(
                        episode_count=F("episode_count") + 1
                    )

                    return GetCreateResult(episode, True)

            # URL could not be created, so it was created since the first get
            except IntegrityError:
                episode = Episode.objects.get(
                    urls__url=url, urls__scope=podcast.as_scope
                )
                return GetCreateResult(episode, False)


class Episode(
    UUIDModel,
    TitleModel,
    DescriptionModel,
    LinkModel,
    LanguageModel,
    LastUpdateModel,
    UpdateInfoModel,
    LicenseModel,
    FlattrModel,
    ContentTypesModel,
    MergedIdsModel,
    OutdatedModel,
    AuthorModel,
    UrlsMixin,
    SlugsMixin,
    MergedUUIDsMixin,
    OptionallyOrderedModel,
):
    """ An episode """

    guid = models.CharField(max_length=200, null=True)
    content = models.TextField()
    released = models.DateTimeField(null=True, db_index=True)
    duration = models.BigIntegerField(null=True)
    filesize = models.BigIntegerField(null=True)
    mimetypes = models.CharField(max_length=200)
    podcast = models.ForeignKey(Podcast, on_delete=models.PROTECT)
    listeners = models.PositiveIntegerField(null=True, db_index=True)

    objects = EpisodeManager()

    class Meta:
        ordering = ["-order", "-released"]

        index_together = [
            ("podcast", "outdated", "released"),
            ("podcast", "released"),
            ("released", "podcast"),
            # index for typical episode toplist queries
            ("language", "listeners"),
            ("podcast", "order", "released"),
        ]

    @property
    def scope(self):
        """ An episode's scope is its podcast """
        return self.podcast.id.hex

    @property
    def display_title(self):
        # TODO: return basename of URL (see Podcast.display_title)
        return self.title

    def get_short_title(self, common_title):
        """ Title when used within the podcast's context """
        if not self.title or not common_title:
            return None

        title = self.title.replace(common_title, "").strip()
        title = re.sub(r"^[\W\d]+", "", title)
        return title

    def get_episode_number(self, common_title):
        """ Number of the episode """
        if not self.title or not common_title:
            return None

        title = self.title.replace(common_title, "").strip()
        match = re.search(r"^\W*(\d+)", title)
        if not match:
            return None

        return int(match.group(1))


class Tag(models.Model):
    """Tags any kind of Model

    See also :class:`TagsMixin`
    """

    FEED = 1
    DELICIOUS = 2
    USER = 4

    SOURCE_CHOICES = ((FEED, "Feed"), (DELICIOUS, "delicious"), (USER, "User"))

    tag = models.SlugField()

    # indicates where the tag came from
    source = models.PositiveSmallIntegerField(choices=SOURCE_CHOICES)

    # the user that created the tag (if it was created by a user,
    # null otherwise)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE
    )

    # see https://docs.djangoproject.com/en/1.6/ref/contrib/contenttypes/#generic-relations
    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.UUIDField()
    content_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        unique_together = (
            # a tag can only be assigned once from one source to one item
            ("tag", "source", "user", "content_type", "object_id"),
        )
