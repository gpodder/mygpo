from collections import Counter

from mygpo.cel import celery
from mygpo.core.slugs import get_duplicate_slugs, EpisodeSlug
from mygpo.maintenance.merge import PodcastMerger
from mygpo.db.couchdb.podcast import podcasts_by_id
from mygpo.db.couchdb.episode import episodes_for_podcast_uncached

from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)


@celery.task
def merge_podcasts(podcast_ids, num_groups):
    """ Task to merge some podcasts"""

    logger.info('merging podcast ids %s', podcast_ids)

    podcasts = podcasts_by_id(podcast_ids)

    logger.info('merging podcasts %s', podcasts)

    actions = Counter()

    pm = PodcastMerger(podcasts, actions, num_groups)
    podcast = pm.merge()

    logger.info('merging result: %s', actions)

    return actions, podcast


@celery.task
def unify_slugs(podcast):
    """ Removes duplicate slugs of a podcast's episodes """

    logger.warn('unifying slugs for podcast %s', podcast)
    episodes = episodes_for_podcast_uncached(podcast)
    logger.info('found %d episodes', len(episodes))

    common_title = podcast.get_common_episode_title()
    actions = Counter()

    # get episodes with duplicate slugs
    for slug, dups in get_duplicate_slugs(episodes):
        actions['dup-slugs'] += 1
        # and remove their slugs
        logger.info('Found %d duplicates for slug %s', len(dups), slug)
        for dup in dups:
            actions['dup-episodes'] += 1

            # check if we're removing the "main" slug
            if dup.slug == slug:

                # if possible, replace it with a "merged" slug
                if dup.merged_slugs:
                    dup.slug = dup.merged_slugs.pop()
                    actions['replaced-with-merged'] += 1
                    logger.info('Replacing slug with merged slug %s', dup.slug)

                # try to find a new slug
                else:
                    dup.slug = EpisodeSlug(dup, common_title,
                        override_existing=True).get_slug()
                    actions['replaced-with-new'] += 1
                    logger.info('Replacing slug with new slug %s', dup.slug)

            # if the problematic slug is a merged one, remove it
            if slug in dup.merged_slugs:
                actions['removed-merged'] += 1
                logger.info('Removing merged slug %s', slug)
                dup.merged_slugs.remove(slug)

            dup.save()

    return actions, podcast
