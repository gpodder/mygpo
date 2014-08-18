from itertools import chain, imap as map
import logging
from functools import partial

import restkit

from django.db import IntegrityError

from mygpo.podcasts.models import MergedUUID, ScopedModel, OrderedModel
from mygpo import utils
from mygpo.decorators import repeat_on_conflict
from mygpo.db.couchdb.podcast_state import all_podcast_states, \
    delete_podcast_state, update_podcast_state_podcast, merge_podcast_states
from mygpo.db.couchdb.episode_state import all_episode_states, \
    update_episode_state_object, add_episode_actions, delete_episode_state, \
    merge_episode_states

import logging
logger = logging.getLogger(__name__)


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
                        "can't merge podcast %s into itself %s" % (podcast1.get_id(), podcast2.get_id()))

        self.podcasts = podcasts
        self.actions = actions
        self.groups = groups

    def merge(self):
        """ Carries out the actual merging """

        logger.info('Start merging of podcasts: %r', self.podcasts)

        podcast1 = self.podcasts.pop(0)
        logger.info('Merge target: %r', podcast1)

        self.merge_episodes()

        for podcast2 in self.podcasts:
            logger.info('Merging %r into target', podcast2)
            self.merge_states(podcast1, podcast2)
            self.reassign_episodes(podcast1, podcast2)
            self._merge_objs(podcast1=podcast1, podcast2=podcast2)
            logger.info('Deleting %r', podcast2)
            podcast2.delete()
            self.actions['merge-podcast'] += 1

        return podcast1

    def merge_episodes(self):
        """ Merges the episodes according to the groups """

        for n, episodes in self.groups:
            if not episodes:
                continue

            episode = episodes.pop(0)
            for ep in episodes:
                em = EpisodeMerger(episode, ep, self.actions)
                em.merge()

    def _merge_objs(self, podcast1, podcast2):
        reassign_merged_uuids(podcast1, podcast2)
        reassign_slugs(podcast1, podcast2)
        reassign_urls(podcast1, podcast2)
        podcast1.content_types = ','.join(podcast1.content_types.split(',') +
                                          podcast2.content_types.split(','))
        podcast1.save()


    def reassign_episodes(self, podcast1, podcast2):

        logger.info('Re-assigning episodes of %r into %r', podcast2, podcast1)

        # re-assign episodes to new podcast
        # if necessary, they will be merged later anyway
        for e in podcast2.episode_set.all():
            self.actions['reassign-episode'] += 1

            for s in all_episode_states(e):
                self.actions['reassign-episode-state'] += 1

                update_episode_state_object(s, podcast1.get_id())

            # TODO: change scopes?
            e.podcast = podcast1
            e.save()

    def merge_states(self, podcast1, podcast2):
        """Merges the Podcast states that are associated with the two Podcasts.

        This should be done after two podcasts are merged
        """

        key = lambda x: x.user
        states1 = sorted(all_podcast_states(podcast1), key=key)
        states2 = sorted(all_podcast_states(podcast2), key=key)

        logger.info('Merging %d podcast states of %r into %r', len(states2),
            podcast2, podcast1)

        for state, state2 in utils.iterate_together([states1, states2], key):

            if state == state2:
                continue

            if state is None:
                self.actions['move-podcast-state'] += 1
                update_podcast_state_podcast(state2, podcast1.get_id(),
                    podcast1.url)

            elif state2 is None:
                continue

            else:
                psm = PodcastStateMerger(state, state2, self.actions)
                psm.merge()


class EpisodeMerger(object):
    """ Merges two episodes """

    def __init__(self, episode1, episode2, actions):
        """ episode2 will be merged into episode1 """

        if episode1 == episode2:
            raise IncorrectMergeException("can't merge episode into itself")

        self.episode1 = episode1
        self.episode2 = episode2
        self.actions = actions

    def merge(self):
        logger.info('Merging episode %r into %r', self.episode2, self.episode1)
        self._merge_objs(episode1=self.episode1, episode2=self.episode2)
        self.merge_states(self.episode1, self.episode2)
        logger.info('Deleting %r', self.episode2)
        self.episode2.delete()
        self.actions['merge-episode'] += 1

    def _merge_objs(self, episode1, episode2):
        reassign_urls(episode1, episode2)
        reassign_merged_uuids(episode1, episode2)
        reassign_slugs(episode1, episode2)


    def merge_states(self, episode, episode2):
        key = lambda x: x.user
        states1 = sorted(all_episode_states(self.episode1), key=key)
        states2 = sorted(all_episode_states(self.episode2), key=key)

        logger.info('Merging %d episode states of %r into %r', len(states2),
                        episode2, episode)

        for state, state2 in utils.iterate_together([states1, states2], key):
            if state == state2:
                continue

            if state is None:
                self.actions['move-episode-state'] += 1
                update_episode_state_object(state2,
                    self.episode1.podcast.get_id(),
                    self.episode1.get_id())

            elif state2 is None:
                continue

            else:
                esm = EpisodeStateMerger(state, state2, self.actions)
                esm.merge()


class PodcastStateMerger(object):
    """Merges the two given podcast states"""

    def __init__(self, state, state2, actions):

        if state._id == state2._id:
            raise IncorrectMergeException(
                "can't merge podcast state into itself")

        if state.user != state2.user:
            raise IncorrectMergeException(
                "states don't belong to the same user")

        self.state = state
        self.state2 = state2
        self.actions = actions

    def merge(self):
        merge_podcast_states(self.state, self.state2)
        self._add_actions(state=self.state, actions=self.state2.actions)
        delete_podcast_state(self.state2)
        self.actions['merged-podcast-state'] += 1


    def _add_actions(self, state, actions):
        try:
            add_episode_actions(state, actions)
        except restkit.Unauthorized:
            # the merge could result in an invalid list of
            # subscribe/unsubscribe actions -- we ignore it and
            # just use the actions from state
            return


class EpisodeStateMerger(object):
    """ Merges state2 in state """

    def __init__(self, state, state2, actions):

        if state._id == state2._id:
            raise IncorrectMergeException(
                "can't merge episode state into itself")

        if state.user != state2.user:
            raise IncorrectMergeException(
                "states don't belong to the same user")

        self.state = state
        self.state2 = state2
        self.actions = actions

    def merge(self):
        merge_episode_states(self.state, self.state2)
        delete_episode_state(self.state2)
        self.actions['merge-episode-state'] += 1


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



def merge(obj1, obj2):
    """ Merges obj2 into obj1 """

    if type(obj1) != type(obj2):
        raise ValueError('Only two objects of the same type can be merged')

    if obj1 == obj2:
        raise ValueError('Cannot merge an object with itself')

    # first we need to move all objects that point to obj2 over to obj1
    # relations can either be "direct" relations or generic ones

    # we iterate over all models that relate to obj2 (eg an Episode refers to
    # a Podcast)
    for rel_obj in obj2._meta.get_all_related_objects():

        # we can access the relating objects from obj2, eg a Podcast has a
        # episode_set
        accessor_name = rel_obj.get_accessor_name()

        # then we need to update the relating obj's relating field (eg
        # Episode.podcast) to obj1
        rel_field = rel_obj.field.name

        objs = getattr(obj2, accessor_name).all()
        for obj in objs:

            if isinstance(obj, ScopedModel):
                obj.scope = obj.get_default_scope()

            if isinstance(obj, OrderedModel):
                obj1_objs = getattr(obj1, accessor_name).all()
                obj.order = max([o.order for o in obj1_objs] + [-1]) + 1

            logger.info("Setting {obj}'s {field} to {obj1}".format(obj=obj,
                field=rel_field, obj1=obj1))
            setattr(obj, rel_field, obj1)
            obj.save()

        # TODO: update scope, ordered models, etc

    for vf in obj2._meta.virtual_fields:
        accessor_name = vf.get_attname()
        fk_field, target_field = vf.resolve_related_fields()[0]

        objs = getattr(obj2, accessor_name).all()
        for obj in objs:

            if isinstance(obj, ScopedModel):
                obj.scope = obj.get_default_scope()

            if isinstance(obj, OrderedModel):
                obj1_objs = getattr(obj1, accessor_name).all()
                obj.order = max([o.order for o in obj1_objs] + [-1]) + 1

            obj1_id = getattr(obj1, target_field.name)
            logger.info("Setting {obj}'s {field} to {obj1}".format(obj=obj,
                field=fk_field, obj1=obj1_id))
            setattr(obj, fk_field.name, obj1_id)
            obj.save()

    obj2.delete()
