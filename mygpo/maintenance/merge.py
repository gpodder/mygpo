from mygpo.core.models import Podcast, Episode
from mygpo.users.models import PodcastUserState
from mygpo import utils



def merge_objects():
    """
    Merges objects (podcasts, podcast states, episodes) based on different criteria
    """

    # The "smaller" podcast is merged into the "greater"
    podcast_merge_order = lambda a, b: cmp(a.subscriber_count(), b.subscriber_count())
    no_merge_order = lambda a, b: 0

    print 'Merging Podcasts by URL'
    podcasts, total = get_view_count_iter(Podcast, 'core/podcasts_by_url')
    merge_from_iterator(podcasts, similar_urls, podcast_merge_order, total, merge_podcasts)

    print 'Merging Podcasts by Old-Id'
    podcasts, total = get_view_count_iter(Podcast, 'core/podcasts_by_oldid')
    merge_from_iterator(podcasts, similar_oldid, podcast_merge_order, total, merge_podcasts)

    print 'Merging Duplicate Podcast States'
    states, total = get_view_count_iter(PodcastUserState, 'users/podcast_states_by_user')
    should_merge = lambda a, b: a == b
    merge_from_iterator(states, should_merge, no_merge_order, total, merge_podcast_states)


    get_episode_merge_data = lambda a, b: dict(podcast=Podcast.for_id(a.podcast), safe_podcast=True)

    print 'Merging Episodes by URL'
    episodes, total = get_view_count_iter(Episode, 'core/episodes_by_url')
    should_merge = lambda a, b: a.podcast == b.podcast and similar_urls(a, b)
    merge_from_iterator(episodes, should_merge, no_merge_order, total, merge_episodes, get_episode_merge_data)

    print 'Merging Episodes by Old-Id'
    episodes, total = get_view_count_iter(Episode, 'core/episodes_by_oldid')
    should_merge = lambda a, b: a.podcast == b.podcast and similar_oldid(a, b)
    merge_from_iterator(episodes, should_merge, no_merge_order, total, merge_episodes, get_episode_merge_data)


def get_view_count_iter(cls, view):
    iterator = cls.view(view).iterator()
    total = cls.view(view, limit=0).total_rows
    return iterator, total


def merge_from_iterator(obj_it, should_merge, cmp, total, merge_func, get_add_merge_data=lambda a, b: {}):
    """
    Iterates over the objects in obj_it and calls should_merge for each pair of
    objects. This implies that the objects returned by obj_it should be sorted
    such that potential merge-candiates appear after each other.

    If should_merge returns True, the pair of objects is going to be merged.
    The smaller object (according to cmp) is merged into the larger one.
    merge_func performs the actual merge. It is passed the two objects to be
    merged (first the larger, then the smaller one) and additional data from
    get_add_merge_data (which should return a dictionary of additional
    parameters to merge_func)
    """

    try:
        prev = obj_it.next()
    except StopIteration:
        return

    for n, p in enumerate(obj_it):
        if should_merge(p, prev):
            print 'merging %s, %s' % (p, prev)
            items = sorted([p, prev], cmp=cmp)
            add_merge_data = get_add_merge_data(*items)
            merge_func(*items, **add_merge_data)

        prev = p
        utils.progress(n, total)


###
#
#  MERGING PODCASTS
#
###

def merge_podcasts(podcast, p):
    """
    Merges p into podcast
    """

    @utils.repeat_on_conflict(['podcast'])
    def do_merge(podcast):
        podcast.merged_ids       = list(set(podcast.merged_ids + [p.get_id()] + p.merged_ids))
        podcast.related_podcasts = list(set(podcast.related_podcasts + p.related_podcasts))
        podcast.content_types    = list(set(podcast.content_types + p.content_types))

        cmp_subscriber_entries = lambda a, b: cmp(a.timestamp, b.timestamp)
        for a, b in utils.iterate_together(podcast.subscribers, p.subscribers, cmp_subscriber_entries):
            if a is None or b is None: continue

            # avoid increasing subscriber_count when merging
            # duplicate entries of a single podcast
            if a.subscriber_count == b.subscriber_count: continue

            a.subscriber_count += b.subscriber_count

        for src, tags in p.tags.values():
            podcast.tags[src] = list(set(podcast.tags.get(src, []) + tags))

        podcast.episodes.update(p.episodes)
        merge_similar_episodes(podcast)

        podcast.save()

    @utils.repeat_on_conflict(['p'])
    def do_delete(p):
        p.delete()

    do_merge(podcast=podcast)
    merge_podcast_states(podcast, p)
    do_delete(p=p)


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


def merge_similar_episodes(podcast):
    EPISODE_SIMILARITY = (similar_urls, similar_oldid)

    for e in podcast.episodes.values():
        for e2 in podcast.episodes.values():
            if e == e2: continue
            if any(sim(e, e2) for sim in EPISODE_SIMILARITY):
                merge_episodes(e, e2, podcast)


def merge_episodes(episode, e, podcast, save_podcast=False):
    episode.urls = list(set(episode.urls + e.urls))
    episode.merged_ids = list(set(episode.merged_ids + [e.id] + e.merged_ids))
    if e.id in podcast.episodes:
        del podcast.episodes[e.id]

    @utils.repeat_on_conflict(['podcast'])
    def save(podcast):
        podcast.save()

    if save_podcast:
        save(podcast=podcast)

###
#
# MERGING PODCAST STATES
#
###

def merge_podcast_states(p1, p2):

    @utils.repeat_on_conflict(['s2'])
    def move(s2, new_id):
        s2.podcast = new_id
        s2.save()

    @utils.repeat_on_conflict(['s1'])
    def merge(s1, s2):
        s1.settings = s2.settings.update(s1.settings)
        s1.add_actions(s2.actions)
        s1.episodes.update(s2.episodes)
        merge_similar_episode_states(p1, s1)
        s1.save()

    @utils.repeat_on_conflict(['s2'])
    def delete(s2):
        s2.delete()

    cmp_states = lambda s1, s2: cmp(s1.user_oldid, s2.user_oldid)
    states1 = p1.get_all_states()
    states2 = p2.get_all_states()
    for s1, s2 in utils.iterate_together(states1, states2, cmp_states):
        if s1 == s2:
            continue

        if s1 == None:
            move(s2=s2, p1.get_id())

        elif s2 == None:
            continue

        else:
            merge(s1=s1, s2=s2)
            delete(s2=s2)

###
#
# MERGING EPISODE STATES
#
###

def merge_similar_episode_states(podcast, podcast_state):
    for e in podcast_state.episodes:
        for e2 in podcast_state.episodes:
            if e == e2: continue
            new_id = find_new_episode_id(podcast, e.id)
            if new_id != e.id:
                merge_episode_states(e, e2, podcast_state)


def find_new_episode_id(podcast, merged_id):
    if merged_id in podcast.episodes.keys():
        return merged_id

    for episode in podcast.episodes.values():
        if merged_id in episode.merged_ids:
            return episode.id

    return None


def merge_episode_states(state, other_state, podcast_state):
    state.add_actions(other_state.actions)
    state.settings.update(other_state.settings)
    if other_state.episode in podcast_state.episodes:
        del podcast_state.episodes[other_state.episode]
