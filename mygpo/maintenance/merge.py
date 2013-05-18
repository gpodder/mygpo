from itertools import chain, imap as map
import logging
from functools import partial

import restkit

from mygpo import utils
from mygpo.decorators import repeat_on_conflict
from mygpo.db.couchdb.podcast import delete_podcast
from mygpo.db.couchdb.episode import episodes_for_podcast
from mygpo.db.couchdb.podcast_state import all_podcast_states, \
    delete_podcast_state
from mygpo.db.couchdb.episode_state import all_episode_states


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
                        "can't merge podcast into itself")

        self.podcasts = podcasts
        self.actions = actions
        self.groups = groups

    def merge(self):
        """ Carries out the actual merging """

        podcast1 = self.podcasts.pop(0)

        for podcast2 in self.podcasts:
            self._merge_objs(podcast1=podcast1, podcast2=podcast2)
            self.merge_states(podcast1, podcast2)
            self.merge_episodes()
            self.reassign_episodes(podcast1, podcast2)
            delete_podcast(podcast2)
            self.actions['merge-podcast'] += 1

        self.merge_episodes()

    def merge_episodes(self):
        """ Merges the episodes according to the groups """

        for n, episodes in self.groups:

            if not episodes:
                continue

            episode = episodes.pop(0)

            for ep in episodes:
                em = EpisodeMerger(episode, ep, self.actions)
                em.merge()

    @repeat_on_conflict(['podcast1', 'podcast2'])
    def _merge_objs(self, podcast1, podcast2):

        podcast1.merged_ids = set_filter(podcast1.get_id(),
                                         podcast1.merged_ids,
                                         [podcast2.get_id()],
                                         podcast2.merged_ids)

        podcast1.merged_slugs = set_filter(podcast1.slug,
                                           podcast1.merged_slugs,
                                           [podcast2.slug],
                                           podcast2.merged_slugs)

        podcast1.merged_oldids = set_filter(podcast1.oldid,
                                            podcast1.merged_oldids,
                                            [podcast2.oldid],
                                            podcast2.merged_oldids)

        # the first URL in the list represents the podcast main URL
        main_url = podcast1.url
        podcast1.urls = set_filter(None, podcast1.urls, podcast2.urls)
        # so we insert it as the first again
        podcast1.urls.remove(main_url)
        podcast1.urls.insert(0, main_url)

        podcast1.content_types = set_filter(None, podcast1.content_types,
                                            podcast2.content_types)

        podcast1.save()

    @repeat_on_conflict(['s'])
    def _save_state(self, s, podcast1):
        s.podcast = podcast1.get_id()
        s.save()

    @repeat_on_conflict(['e'])
    def _save_episode(self, e, podcast1):
        e.podcast = podcast1.get_id()
        e.save()

    def reassign_episodes(self, podcast1, podcast2):
        # re-assign episodes to new podcast
        # if necessary, they will be merged later anyway
        for e in episodes_for_podcast(podcast2):
            self.actions['reassign-episode'] += 1

            for s in all_episode_states(e):
                self.actions['reassign-episode-state'] += 1

                self._save_state(s=s, podcast1=podcast1)

            self._save_episode(e=e, podcast1=podcast1)

    def merge_states(self, podcast1, podcast2):
        """Merges the Podcast states that are associated with the two Podcasts.

        This should be done after two podcasts are merged
        """

        key = lambda x: x.user
        states1 = sorted(all_podcast_states(podcast1), key=key)
        states2 = sorted(all_podcast_states(podcast2), key=key)

        for state, state2 in utils.iterate_together([states1, states2], key):

            if state == state2:
                continue

            if state is None:
                self.actions['move-podcast-state'] += 1
                self._move_state(state2=state2, new_id=podcast1.get_id(),
                                 new_url=podcast1.url)

            elif state2 is None:
                continue

            else:
                psm = PodcastStateMerger(state, state2, self.actions)
                psm.merge()

    @repeat_on_conflict(['state2'])
    def _move_state(self, state2, new_id, new_url):
        state2.ref_url = new_url
        state2.podcast = new_id
        state2.save()


class EpisodeMerger(object):

    def __init__(self, episode1, episode2, actions):
        if episode1 == episode2:
            raise IncorrectMergeException("can't merge episode into itself")

        self.episode1 = episode1
        self.episode2 = episode2
        self.actions = actions

    def merge(self):
        self._merge_objs(episode1=self.episode1, episode2=self.episode2)
        self.merge_states(self.episode1, self.episode2)
        self._delete(e=self.episode2)
        self.actions['merge-episode'] += 1

    @repeat_on_conflict(['episode1'])
    def _merge_objs(self, episode1, episode2):

        episode1.urls = set_filter(None, episode1.urls, episode2.urls)

        episode1.merged_ids = set_filter(episode1._id, episode1.merged_ids,
                                         [episode2._id], episode2.merged_ids)

        episode1.merged_slugs = set_filter(episode1.slug,
                                           episode1.merged_slugs,
                                           [episode2.slug],
                                           episode2.merged_slugs)

        episode1.save()

    @repeat_on_conflict(['e'])
    def _delete(self, e):
        e.delete()

    def merge_states(self, episode, episode2):

        key = lambda x: x.user
        states1 = sorted(all_episode_states(self.episode1), key=key)
        states2 = sorted(all_episode_states(self.episode2), key=key)

        for state, state2 in utils.iterate_together([states1, states2], key):

            if state == state2:
                continue

            if state is None:
                self.actions['move-episode-state'] += 1
                self._move(state2=state2, podcast_id=self.episode1.podcast,
                           episode_id=self.episode1._id)

            elif state2 is None:
                continue

            else:
                esm = EpisodeStateMerger(state, state2, self.actions)
                esm.merge()

    @repeat_on_conflict(['state2'])
    def _move(self, state2, podcast_id, episode_id):
        state2.podcast = podcast_id
        state2.episode = episode_id
        state2.save()


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
        self._do_merge(state=self.state, state2=self.state2)
        self._add_actions(state=self.state, actions=self.state2.actions)
        self._delete(state2=self.state2)
        self.actions['merged-podcast-state'] += 1

    @repeat_on_conflict(['state'])
    def _do_merge(self, state, state2):

        # overwrite settings in state2 with state's settings
        settings = state2.settings
        settings.update(state.settings)
        state.settings = settings

        state.disabled_devices = set_filter(None, state.disabled_devices,
                                            state2.disabled_devices)

        state.merged_ids = set_filter(state._id, state.merged_ids,
                                      [state2._id], state2.merged_ids)

        state.tags = set_filter(None, state.tags, state2.tags)

        state.save()

    @repeat_on_conflict(['state'])
    def _add_actions(self, state, actions):
        try:
            state.add_actions(actions)
            state.save()
        except restkit.Unauthorized:
            # the merge could result in an invalid list of
            # subscribe/unsubscribe actions -- we ignore it and
            # just use the actions from state
            return

    @repeat_on_conflict(['state2'])
    def _delete(self, state2):
        state2.delete()


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
        self._merge_obj(state=self.state, state2=self.state2)
        delete_podcast_state(self.state2)
        self.actions['merge-episode-state'] += 1

    @repeat_on_conflict(['state'])
    def _merge_obj(self, state, state2):
        state.add_actions(state2.actions)

        # overwrite settings in state2 with state's settings
        settings = state2.settings
        settings.update(state.settings)
        state.settings = settings

        merged_ids = set(state.merged_ids + [state2._id] + state2.merged_ids)
        state.merged_ids = filter(None, merged_ids)

        state.chapters = list(set(state.chapters + state2.chapters))

        state.save()


def set_filter(orig, *args):
    """ chain args, and remove falsy values and orig """
    s = set(chain.from_iterable(args))
    s = s - set([orig])
    s = filter(None, s)
    return s
