from itertools import chain, imap
import logging
from functools import partial

import restkit

from mygpo.core.models import Podcast, Episode, PodcastGroup
from mygpo.users.models import PodcastUserState, EpisodeUserState
from mygpo import utils
from mygpo.decorators import repeat_on_conflict


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

def podcast_oldid_wrapper(r):
    oldid = r['key']
    doc = r['doc']
    if doc['doc_type'] == 'Podcast':
        obj = Podcast.wrap(doc)
    elif doc['doc_type'] == 'PodcastGroup':
        obj = PodcastGroup.wrap(doc)

    return obj.get_podcast_by_oldid(oldid)


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
                'core/podcasts_by_url',
                wrap = False,
                include_docs=True)
        podcasts = imap(podcast_url_wrapper, podcasts)
        merger(podcasts, similar_urls, podcast_merge_order, total,
                merge_podcasts)
        print


        print 'Merging Podcasts by Old-Id'
        podcasts, total = get_view_count_iter(Podcast,
                'core/podcasts_by_oldid',
                wrap = False,
                include_docs=True)
        podcasts = imap(podcast_oldid_wrapper, podcasts)
        merger(podcasts, similar_oldid, podcast_merge_order, total,
                merge_podcasts)
        print


    if podcast_states:
        print 'Merging Duplicate Podcast States'
        states, total = get_view_count_iter(PodcastUserState,
                'users/podcast_states_by_user',
                include_docs=True)
        should_merge = lambda a, b: a == b
        merger(states, should_merge, no_merge_order, total,
                merge_podcast_states)
        print


    if episodes:
        print 'Merging Episodes by URL'
        episodes, total = get_view_count_iter(Episode,
                'core/episodes_by_podcast_url',
                include_docs=True)
        should_merge = lambda a, b: a.podcast == b.podcast and \
                similar_urls(a, b)
        merger(episodes, should_merge, no_merge_order, total, merge_episodes)
        print


        print 'Merging Episodes by Old-Id'
        episodes, total = get_view_count_iter(Episode,
                'core/episodes_by_oldid',
                include_docs=True)
        should_merge = lambda a, b: a.podcast == b.podcast and \
                similar_oldid(a, b)
        merger(episodes, should_merge, no_merge_order, total, merge_episodes)
        print


    if episode_states:
        print 'Merging Duplicate Episode States'
        states, total = get_view_count_iter(EpisodeUserState,
                'users/episode_states_by_user_episode',
                include_docs=True)
        should_merge = lambda a, b: (a.user_oldid, a.episode) == \
                                    (b.user_oldid, b.episode)
        merger(states, should_merge, no_merge_order, total,
                merge_episode_states)
        print



def get_view_count_iter(cls, view, *args, **kwargs):
    iterator = utils.multi_request_view(cls, view, *args, **kwargs)
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


###
#
#  MERGING PODCASTS
#
###

def merge_podcasts(podcast, podcast2, dry_run=False):
    """
    Merges podcast2 into podcast
    """

    @repeat_on_conflict(['podcast'], reload_f=lambda p:Podcast.get(p.get_id()))
    def _do_merge(podcast, podcast2):

        podcast.merged_ids = set_filter(podcast.merged_ids,
                [podcast2.get_id()], podcast2.merged_ids)

        podcast.merged_slugs = set_filter(podcast.merged_slugs,
                [podcast2.slug], podcast2.merged_slugs)

        podcast.merged_oldids = set_filter(podcast.merged_oldids,
                [podcast2.oldid], podcast2.merged_oldids)

        # the first URL in the list represents the podcast main URL
        main_url = podcast.url
        podcast.urls = set_filter(podcast.urls, podcast2.urls)
        # so we insert it as the first again
        podcast.urls.remove(main_url)
        podcast.urls.insert(0, main_url)

        # we ignore related_podcasts because
        # * the elements should be roughly the same
        # * element order is important but could not preserved exactly

        podcast.content_types = set_filter(podcast.content_types,
                podcast2.content_types)

        key = lambda x: x.timestamp
        for a, b in utils.iterate_together(
                [podcast.subscribers, podcast2.subscribers], key):

            if a is None or b is None: continue

            # avoid increasing subscriber_count when merging
            # duplicate entries of a single podcast
            if a.subscriber_count == b.subscriber_count:
                continue

            a.subscriber_count += b.subscriber_count

        for src, tags in podcast2.tags.items():
            podcast.tags[src] = set_filter(podcast.tags.get(src, []), tags)

        podcast.save()


    @repeat_on_conflict(['podcast2'])
    def _do_delete(podcast2):
        podcast2.delete()


    # re-assign episodes to new podcast
    # if necessary, they will be merged later anyway
    for e in podcast2.get_episodes():

        @repeat_on_conflict(['s'])
        def save_state(s):
            s.podcast = podcast.get_id()
            s.save()


        @repeat_on_conflict(['e'])
        def save_episode(e):
            e.podcast = podcast.get_id()
            e.save()

        for s in e.get_all_states():
            save_state(s=s)

        save_episode(e=e)


    _do_merge(podcast=podcast, podcast2=podcast2)
    merge_podcast_states_for_podcasts(podcast, podcast2, dry_run=dry_run)
    _do_delete(podcast2=podcast2)

    # Merge Episode States
    no_merge_order = lambda a, b: 0
    episodes = sorted(podcast.get_episodes(), key=lambda e: e.url)
    should_merge = lambda a, b: a.podcast == b.podcast and similar_urls(a, b)

    merge_from_iterator(episodes, should_merge, no_merge_order, len(episodes),
            merge_episodes)


def similar_urls(a, b):
    """ Two Podcasts/Episodes are merged, if they have the same URLs"""
    return bool(utils.intersect(a.urls, b.urls))


def similar_oldid(o1, o2):
    """ Two Podcasts/Episodes are merged, if they have the same Old-IDs"""
    return o1.oldid == o2.oldid and o1.oldid is not None


###
#
# MERGING EPISODES
#
###


def merge_episodes(episode, e, dry_run=False):

    episode.urls = set_filter(episode.urls, e.urls)

    episode.merged_ids = set_filter(episode.merged_ids, [e._id],
            e.merged_ids)

    episode.merged_slugs = set_filter(episode.merged_slugs, [e.slug],
            e.merged_slugs)

    @repeat_on_conflict(['e'])
    def delete(e):
        e.delete()

    @repeat_on_conflict(['episode'])
    def save(episode):
        episode.save()

    merge_episode_states_for_episodes(episode, e, dry_run)

    save(episode=episode)
    delete(e=e)



###
#
# MERGING PODCAST STATES
#
###

def merge_podcast_states_for_podcasts(podcast, podcast2, dry_run=False):
    """Merges the Podcast states that are associated with the two Podcasts.

    This should be done after two podcasts are merged
    """

    @repeat_on_conflict(['state2'])
    def move(state2, new_id, new_url):
        state2.ref_url = new_url
        state2.podcast = new_id
        state2.save()

    @repeat_on_conflict(['state2'])
    def _delete(state2):
        state2.delete()

    key = lambda x: x.user_oldid
    states1 = podcast.get_all_states()
    states2 = podcast2.get_all_states()

    for state, state2 in utils.iterate_together([states1, states2], key):

        if state == state2:
            continue

        if state == None:
            _move(state2=state2, new_id=podcast.get_id(), new_url=podcast.url)

        elif state2 == None:
            continue

        else:
            merge_podcast_states(state, state2)
            delete(state2=state2)


def merge_podcast_states(state, state2):
    """Merges the two given podcast states"""

    if state.user_oldid != state2.user_oldid:
        raise IncorrectMergeException("states don't belong to the same user")

    @repeat_on_conflict(['state'])
    def _do_merge(state, state2):

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
    def _add_actions(state, actions):
        try:
            state.add_actions(actions)
            state.save()
        except restkit.Unauthorized:
            # the merge could result in an invalid list of
            # subscribe/unsubscribe actions -- we ignore it and
            # just use the actions from state
            return

    @repeat_on_conflict(['state2'])
    def _do_delete(state2):
        state2.delete()

    _do_merge(state=state, state2=state2)

    _add_actions(state=state, actions=state2.actions)

    _do_delete(state2=state2)


###
#
# MERGING EPISODE STATES
#
###


def merge_episode_states_for_episodes(episode, episode2, dry_run=False):

    @repeat_on_conflict(['state2'])
    def move(state2, podcast_id, episode_id):
        state2.podcast = podcast_id
        state2.episode = episode_id
        state2.save()

    key = lambda x: x.user_oldid
    states1 = episode.get_all_states()
    states2 = episode2.get_all_states()

    for state, state2 in utils.iterate_together([states1, states2], key):

        if state == state2:
            continue

        if state == None:
            _move(state2=state2, podcast_id=episode.podcast,
                    episode_id=episode._id)

        elif state2 == None:
            continue

        else:
            merge_episode_states(state, state2)



def merge_episode_states(state, state2):
    """ Merges state2 in state """

    if state.user_oldid != state2.user_oldid:
        raise IncorrectMergeException("states don't belong to the same user")


    @repeat_on_conflict(['state'])
    def _do_update(state, state2):
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
    def _do_delete(state2):
        state2.delete()

    _do_update(state=state, state2=state2)
    _do_delete(state2=state2)


def set_filter(*args):
    return filter(None, set(chain.from_iterable(args)))
