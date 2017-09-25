import collections

from django.db import transaction, IntegrityError
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model
from django.apps import apps
from django.contrib.contenttypes.fields import GenericForeignKey

from mygpo.podcasts.models import (MergedUUID, ScopedModel, OrderedModel, Slug,
                                   Tag, URL, MergedUUID, Podcast, Episode)
from mygpo import utils
from mygpo.history.models import HistoryEntry, EpisodeHistoryEntry
from mygpo.publisher.models import PublishedPodcast
from mygpo.subscriptions.models import Subscription

import logging
logger = logging.getLogger(__name__)


PG_UNIQUE_VIOLATION = 23505


class IncorrectMergeException(Exception):
    pass


class PodcastMerger(object):
    """ Merges podcasts and their related objects """

    def __init__(self, podcasts, actions, groups):
        """ Prepares to merge podcasts[1:] into podcasts[0]  """

        for n, podcast1 in enumerate(podcasts):
            for m, podcast2 in enumerate(podcasts):
                if podcast1 == podcast2 and n != m:
                    raise IncorrectMergeException(
                        "can't merge podcast %s into itself %s" %
                        (podcast1.get_id(), podcast2.get_id()))

        self.podcasts = podcasts
        self.actions = actions
        self.groups = groups

    def merge(self):
        """ Carries out the actual merging """

        logger.info('Start merging of podcasts: %r', self.podcasts)

        podcast1 = self.podcasts.pop(0)
        logger.info('Merge target: %r', podcast1)

        self.merge_episodes()
        merge_model_objects(podcast1, self.podcasts)

        return podcast1

    def merge_episodes(self):
        """ Merges the episodes according to the groups """

        for n, episodes in self.groups:
            if not episodes:
                continue

            episode = episodes.pop(0)
            logger.info('Merging %d episodes', len(episodes))
            merge_model_objects(episode, episodes)


def reassign_urls(obj1, obj2):
    # Reassign all URLs of obj2 to obj1
    max_order = max([0] + [u.order for u in obj1.urls.all()])

    for n, url in enumerate(obj2.urls.all(), max_order+1):
        url.content_object = obj1
        url.order = n
        url.scope = obj1.scope
        try:
            url.save()
        except IntegrityError as ie:
            logger.warn('Moving URL failed: %s. Deleting.', str(ie))
            url.delete()


def reassign_merged_uuids(obj1, obj2):
    # Reassign all IDs of obj2 to obj1
    MergedUUID.objects.create(uuid=obj2.id, content_object=obj1)
    for m in obj2.merged_uuids.all():
        m.content_object = obj1
        m.save()


def reassign_slugs(obj1, obj2):
    # Reassign all Slugs of obj2 to obj1
    max_order = max([0] + [s.order for s in obj1.slugs.all()])
    for n, slug in enumerate(obj2.slugs.all(), max_order+1):
        slug.content_object = obj1
        slug.order = n
        slug.scope = obj1.scope
        try:
            slug.save()
        except IntegrityError as ie:
            logger.warn('Moving Slug failed: %s. Deleting', str(ie))
            slug.delete()


# based on https://djangosnippets.org/snippets/2283/
@transaction.atomic
def merge_model_objects(primary_object, alias_objects=[], keep_old=False):
    """
    Use this function to merge model objects (i.e. Users, Organizations, Polls,
    etc.) and migrate all of the related fields from the alias objects to the
    primary object.

    Usage:
    from django.contrib.auth.models import User
    primary_user = User.objects.get(email='good_email@example.com')
    duplicate_user = User.objects.get(email='good_email+duplicate@example.com')
    merge_model_objects(primary_user, duplicate_user)
    """
    if not isinstance(alias_objects, list):
        alias_objects = [alias_objects]

    # check that all aliases are the same class as primary one and that
    # they are subclass of model
    primary_class = primary_object.__class__

    if not issubclass(primary_class, Model):
        raise TypeError('Only django.db.models.Model subclasses can be merged')

    for alias_object in alias_objects:
        if not isinstance(alias_object, primary_class):
            raise TypeError('Only models of same class can be merged')

    # Get a list of all GenericForeignKeys in all models
    # TODO: this is a bit of a hack, since the generics framework should
    # provide a similar method to the ForeignKey field for accessing the
    # generic related fields.
    generic_fields = []
    for model in apps.get_models():
        fields = filter(lambda x: isinstance(x[1], GenericForeignKey),
                        model.__dict__.items())
        for field_name, field in fields:
            generic_fields.append(field)

    blank_local_fields = set(
        [field.attname for field
         in primary_object._meta.local_fields
         if getattr(primary_object, field.attname) in [None, '']])

    # Loop through all alias objects and migrate their data to
    # the primary object.
    for alias_object in alias_objects:
        # Migrate all foreign key references from alias object to
        # primary object.
        for related_object in _get_all_related_objects(alias_object):
            # The variable name on the alias_object model.
            alias_varname = related_object.get_accessor_name()
            # The variable name on the related model.
            obj_varname = related_object.field.name
            related_objects = getattr(alias_object, alias_varname)
            for obj in related_objects.all():
                setattr(obj, obj_varname, primary_object)
                reassigned(obj, primary_object)
                obj.save()

        # Migrate all many to many references from alias object to
        # primary object.
        related = _get_all_related_many_to_many_objects(alias_object)
        for related_many_object in related:
            alias_varname = related_many_object.get_accessor_name()
            obj_varname = related_many_object.field.name

            if alias_varname is not None:
                # standard case
                related_many_objects = getattr(alias_object,
                                               alias_varname).all()
            else:
                # special case, symmetrical relation, no reverse accessor
                related_many_objects = getattr(alias_object,
                                               obj_varname).all()
            for obj in related_many_objects.all():
                getattr(obj, obj_varname).remove(alias_object)
                reassigned(obj, primary_object)
                getattr(obj, obj_varname).add(primary_object)

        # Migrate all generic foreign key references from alias
        # object to primary object.
        for field in generic_fields:
            filter_kwargs = {}
            filter_kwargs[field.fk_field] = alias_object._get_pk_val()
            filter_kwargs[field.ct_field] = field.get_content_type(
                alias_object)
            related = field.model.objects.filter(**filter_kwargs)
            for generic_related_object in related:
                setattr(generic_related_object, field.name, primary_object)
                reassigned(generic_related_object, primary_object)
                try:
                    # execute save in a savepoint, so we can resume in the
                    # transaction
                    with transaction.atomic():
                        generic_related_object.save()
                except IntegrityError as ie:
                    if ie.__cause__.pgcode == PG_UNIQUE_VIOLATION:
                        merge(generic_related_object, primary_object)

        # Try to fill all missing values in primary object by
        # values of duplicates
        filled_up = set()
        for field_name in blank_local_fields:
            val = getattr(alias_object, field_name)
            if val not in [None, '']:
                setattr(primary_object, field_name, val)
                filled_up.add(field_name)
        blank_local_fields -= filled_up

        if not keep_old:
            before_delete(alias_object, primary_object)
            alias_object.delete()
    primary_object.save()
    return primary_object


def _get_all_related_objects(obj):
    return [
        f for f in obj._meta.get_fields()
        if (f.one_to_many or f.one_to_one) and
        f.auto_created and not f.concrete
    ]


def _get_all_related_many_to_many_objects(obj):
    return [
        f for f in obj._meta.get_fields(include_hidden=True)
        if f.many_to_many and f.auto_created
    ]


def reassigned(obj, new):
    if isinstance(obj, URL):
        # a URL has its parent's scope
        obj.scope = new.scope

        existing_urls = new.urls.all()
        max_order = max([-1] + [u.order for u in existing_urls])
        obj.order = max_order+1

    elif isinstance(obj, Episode):
        # obj is an Episode, new is a podcast
        for url in obj.urls.all():
            url.scope = new.as_scope
            url.save()

    elif isinstance(obj, Subscription):
        pass

    elif isinstance(obj, EpisodeHistoryEntry):
        pass

    elif isinstance(obj, HistoryEntry):
        pass

    else:
        raise TypeError('unknown type for reassigning: {objtype}'.format(
            objtype=type(obj)))


def before_delete(old, new):

    if isinstance(old, Episode):
        MergedUUID.objects.create(
            content_type=ContentType.objects.get_for_model(new),
            object_id=new.pk,
            uuid=old.pk,
        )

    elif isinstance(old, Podcast):
        MergedUUID.objects.create(
            content_type=ContentType.objects.get_for_model(new),
            object_id=new.pk,
            uuid=old.pk,
        )

    else:
        raise TypeError('unknown type for deleting: {objtype}'.format(
            objtype=type(old)))


def merge(moved_obj, new_target):
    if isinstance(moved_obj, URL):
        # if we have two conflicting URLs, don't save the second one
        # URLs don't have any interesting properties (except the URL) that
        # we could merge
        pass

    else:
        raise TypeError('unknown type for merging: {objtype}'.format(
            objtype=type(old)))
