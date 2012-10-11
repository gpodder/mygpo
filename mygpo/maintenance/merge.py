from itertools import chain, imap as map
import logging
from functools import partial

import restkit

from mygpo.core.models import Podcast, Episode, PodcastGroup
from mygpo.users.models import PodcastUserState, EpisodeUserState
from mygpo import utils
from mygpo.decorators import repeat_on_conflict
from mygpo.db.couchdb.episode import episodes_for_podcast
from mygpo.db.couchdb.podcast_state import all_podcast_states
from mygpo.db.couchdb.episode_state import all_episode_states
from mygpo.db.couchdb.utils import multi_request_view


class IncorrectMergeException(Exception):
    pass


def podcast_url_wrapper(r):
    url = r['key']
    doc = r['doc']
    if doc['doc_type'] == 'Podcast':
        obj = Podcast.wrap(doc)
    elif doc['doc_type'] == 'PodcastGroup':
        obj = PodcastGroup.wrap(doc)

    return obj.get_podcast_by_url(url)


def merge_objects(podcasts=True, podcast_states=False, episodes=False,
        episode_states=False, dry_run=False):
    """
    Merges objects (podcasts, episodes, states) based on different criteria
    """

    # The "smaller" podcast is merged into the "greater"
    podcast_merge_order = lambda a, b: cmp(a.subscriber_count(), b.subscriber_count())
    no_merge_order = lambda a, b: 0

    merger = partial(merge_from_iterator, dry_run=dry_run,
            progress_callback=utils.progress)


    if podcasts:

        print 'Merging Podcasts by URL'
        podcasts, total = get_view_count_iter(Podcast,
                'podcasts/by_url',
                wrap = False,
                include_docs=True)
        podcasts = map(podcast_url_wrapper, podcasts)
        merger(podcasts, similar_urls, podcast_merge_order, total,
                merge_podcasts)
        print


        print 'Merging Podcasts by Old-Id'
        podcasts, total = get_view_count_iter(Podcast,
                'podcasts/by_oldid',
                wrap = False,
                include_docs=True)
        podcasts = imap(podcast_oldid_wrapper, podcasts)
        merger(podcasts, similar_oldid, podcast_merge_order, total,
                merge_podcasts)
        print


    if podcast_states:
        print 'Merging Duplicate Podcast States'
        states, total = get_view_count_iter(PodcastUserState,
                'podcast_states/by_user',
                include_docs=True)
        should_merge = lambda a, b: a == b
        merger(states, should_merge, no_merge_order, total,
                merge_podcast_states)
        print


    if episodes:
        print 'Merging Episodes by URL'
        episodes, total = get_view_count_iter(Episode,
                'episodes/by_podcast_url',
                include_docs=True)
        should_merge = lambda a, b: a.podcast == b.podcast and \
                similar_urls(a, b)
        merger(episodes, should_merge, no_merge_order, total, merge_episodes)
        print


        print 'Merging Episodes by Old-Id'
        episodes, total = get_view_count_iter(Episode,
                'episodes/by_oldid',
                include_docs=True)
        should_merge = lambda a, b: a.podcast == b.podcast and \
                similar_oldid(a, b)
        merger(episodes, should_merge, no_merge_order, total, merge_episodes)
        print


    if episode_states:
        print 'Merging Duplicate Episode States'
        states, total = get_view_count_iter(EpisodeUserState,
                'episode_states/by_user_episode',
                include_docs=True)
        should_merge = lambda a, b: (a.user, a.episode) == \
                                    (b.user, b.episode)
        merger(states, should_merge, no_merge_order, total,
                merge_episode_states)
        print



def get_view_count_iter(cls, view, *args, **kwargs):
    iterator = multi_request_view(cls, view, *args, **kwargs)
    total = cls.view(view, limit=0).total_rows
    return iterator, total


def merge_from_iterator(obj_it, should_merge, cmp, total, merge_func,
        dry_run=False, progress_callback=lambda *args, **kwargs: None):
    """
    Iterates over the objects in obj_it and calls should_merge for each pair of
    objects. This implies that the objects returned by obj_it should be sorted
    such that potential merge-candiates appear after each other.

    If should_merge returns True, the pair of objects is going to be merged.
    The smaller object (according to cmp) is merged into the larger one.
    merge_func performs the actual merge. It is passed the two objects to be
    merged (first the larger, then the smaller one).
    """

    obj_it = iter(obj_it)

    try:
        prev = obj_it.next()
    except StopIteration:
        return

    for n, p in enumerate(obj_it):
        if should_merge(p, prev):
            items = sorted([p, prev], cmp=cmp)
            logging.info('merging {old} into {new}'.
                    format(old=items[1], new=items[0]))

            merge_func(*items, dry_run=dry_run)

        prev = p
        progress_callback(n, total)



class PodcastMerger(object):
    """ Merges podcast2 into podcast

    Also merges the related podcast states, and re-assignes podcast2's episodes
    to podcast, but does neither merge their episodes nor their episode states
    """


    def __init__(self, podcasts, actions, groups, dry_run=False):

        for n, podcast1 in enumerate(podcasts):
            for m, podcast2 in enumerate(podcasts):
                if podcast1 == podcast2 and n != m:
                    raise IncorrectMergeException("can't merge podcast into itself")

        self.podcasts = podcasts
        self.actions = actions
        self.groups = groups
        self.dry_run = dry_run


    def merge(self):
        podcast1 = self.podcasts.pop(0)

        for podcast2 in self.podcasts:
            self._merge_objs(podcast1=podcast1, podcast2=podcast2)
            self.merge_states(podcast1, podcast2)
            self.merge_episodes()
            self.reassign_episodes(podcast1, podcast2)
            self._delete(podcast2=podcast2)

        self.actions['merge-podcast'] += 1


    def merge_episodes(self):
        for n, episodes in self.groups:

            episode = episodes.pop(0)

            for ep in episodes:

                em = EpisodeMerger(episode, ep, self.actions)
                em.merge()


    @repeat_on_conflict(['podcast1', 'podcast2'])
    def _merge_objs(self, podcast1, podcast2):

        podcast1.merged_ids = set_filter(podcast1.merged_ids,
                [podcast2.get_id()], podcast2.merged_ids)

        podcast1.merged_slugs = set_filter(podcast1.merged_slugs,
                [podcast2.slug], podcast2.merged_slugs)

        podcast1.merged_oldids = set_filter(podcast1.merged_oldids,
                [podcast2.oldid], podcast2.merged_oldids)

        # the first URL in the list represents the podcast main URL
        main_url = podcast1.url
        podcast1.urls = set_filter(podcast1.urls, podcast2.urls)
        # so we insert it as the first again
        podcast1.urls.remove(main_url)
        podcast1.urls.insert(0, main_url)

        # we ignore related_podcasts because
        # * the elements should be roughly the same
        # * element order is important but could not preserved exactly

        podcast1.content_types = set_filter(podcast1.content_types,
                podcast2.content_types)

        key = lambda x: x.timestamp
        for a, b in utils.iterate_together(
                [podcast1.subscribers, podcast2.subscribers], key):

            if a is None or b is None: continue

            # avoid increasing subscriber_count when merging
            # duplicate entries of a single podcast
            if a.subscriber_count == b.subscriber_count:
                continue

            a.subscriber_count += b.subscriber_count

        for src, tags in podcast2.tags.items():
            podcast1.tags[src] = set_filter(podcast1.tags.get(src, []), tags)

        podcast1.save()


    @repeat_on_conflict(['podcast2'])
    def _delete(self, podcast2):
        podcast2.delete()


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

            if state == None:
                self.actions['move-podcast-state'] += 1
                self._move_state(state2=state2, new_id=podcast1.get_id(),
                        new_url=podcast1.url)

            elif state2 == None:
                continue

            else:
                psm = PodcastStateMerger(state, state2, self.actions)
                psm.merge()


    @repeat_on_conflict(['state2'])
    def _move_state(self, state2, new_id, new_url):
        state2.ref_url = new_url
        state2.podcast = new_id
        state2.save()

    @repeat_on_conflict(['state2'])
    def _delete_state(state2):
        state2.delete()




def similar_urls(a, b):
    """ Two Podcasts/Episodes are merged, if they have the same URLs"""
    return bool(utils.intersect(a.urls, b.urls))






class EpisodeMerger(object):


    def __init__(self, episode1, episode2, actions, dry_run=False):
        if episode1 == episode2:
            raise IncorrectMergeException("can't merge episode into itself")

        self.episode1 = episode1
        self.episode2 = episode2
        self.actions = actions
        self.dry_run = dry_run


    def merge(self):
        self._merge_objs(episode1=self.episode1, episode2=self.episode2)
        self.merge_states(self.episode1, self.episode2)
        self._delete(e=self.episode2)
        self.actions['merge-episode'] += 1


    @repeat_on_conflict(['episode1'])
    def _merge_objs(self, episode1, episode2):

        episode1.urls = set_filter(episode1.urls, episode2.urls)

        episode1.merged_ids = set_filter(episode1.merged_ids, [episode2._id],
                episode2.merged_ids)

        episode1.merged_slugs = set_filter(episode1.merged_slugs, [episode2.slug],
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

            if state == None:
                self.actions['move-episode-state'] += 1
                self._move(state2=state2, podcast_id=self.episode1.podcast,
                        episode_id=self.episode1._id)

            elif state2 == None:
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

    def __init__(self, state, state2, actions, dry_run=False):

        if state._id == state2._id:
            raise IncorrectMergeException("can't merge podcast state into itself")

        if state.user != state2.user:
            raise IncorrectMergeException("states don't belong to the same user")

        self.state = state
        self.state2 = state2
        self.actions = actions
        self.dry_run = dry_run


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

        state.disabled_devices = set_filter(state.disabled_devices,
                state2.disabled_devices)

        state.merged_ids = set_filter(state.merged_ids, [state2._id],
                state2.merged_ids)

        state.tags = set_filter(state.tags, state2.tags)

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

    def __init__(self, state, state2, actions, dry_run=False):

        if state._id == state2._id:
            raise IncorrectMergeException("can't merge episode state into itself")

        if state.user != state2.user:
            raise IncorrectMergeException("states don't belong to the same user")

        self.state = state
        self.state2 = state2
        self.actions = actions
        self.dry_run = dry_run


    def merge(self):
        self._merge_obj(state=self.state, state2=self.state2)
        self._do_delete(state2=self.state2)
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

    @repeat_on_conflict(['state2'])
    def _do_delete(self, state2):
        state2.delete()


def set_filter(*args):
    return filter(None, set(chain.from_iterable(args)))
