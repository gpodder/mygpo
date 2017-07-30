#!/usr/bin/python
# -*- coding: utf-8 -*-

import os.path
import urllib.parse
from urllib.parse import urljoin
import hashlib
from datetime import datetime, timedelta
from itertools import chain, islice
import requests

from django.db import transaction
from django.conf import settings

from mygpo.podcasts.models import Podcast, Episode
from mygpo.core.slugs import PodcastSlugs, EpisodeSlugs
from mygpo.podcasts.models import DEFAULT_UPDATE_INTERVAL, \
    MIN_UPDATE_INTERVAL, MAX_UPDATE_INTERVAL
from mygpo.utils import to_maxlength
from mygpo.web.logo import CoverArt
from mygpo.data.podcast import subscribe_at_hub
from mygpo.data.tasks import update_related_podcasts
from mygpo.pubsub.models import SubscriptionError
from mygpo.directory.tags import update_category

import logging
logger = logging.getLogger(__name__)

MAX_EPISODES_UPDATE = 200


class UpdatePodcastException(Exception):
    pass


class NoPodcastCreated(Exception):
    """ raised when no podcast obj was created for a new URL """


class NoEpisodesException(Exception):
    """ raised when parsing something that doesn't contain any episodes """


def update_podcasts(queue):
    """ Fetch data for the URLs supplied as the queue iterable """

    for n, podcast_url in enumerate(queue, 1):
        logger.info('Update %d - %s', n, podcast_url)
        try:
            yield update_podcast(podcast_url)

        except NoPodcastCreated as npc:
            logger.info('No podcast created: %s', npc)

        except:
            logger.exception('Error while updating podcast "%s"',
                             podcast_url)
            raise


def update_podcast(podcast_url):
    """ Update the podcast for the supplied URL """

    try:
        parsed = _fetch_feed(podcast_url)
        _validate_parsed(parsed)

    except requests.exceptions.RequestException as re:
        logging.exception('Error while fetching response from feedservice')

        # if we fail to parse the URL, we don't even create the
        # podcast object
        try:
            p = Podcast.objects.get(urls__url=podcast_url)
            # if it exists already, we mark it as outdated
            _mark_outdated(p, 'error while fetching feed: %s' % str(re))
            p.last_update = datetime.utcnow()
            p.save()
            return p

        except Podcast.DoesNotExist:
            raise NoPodcastCreated(re)

    except NoEpisodesException as nee:
        logging.warn('No episode found while parsing podcast')

        # if we fail to parse the URL, we don't even create the
        # podcast object
        try:
            p = Podcast.objects.get(urls__url=podcast_url)
            # if it exists already, we mark it as outdated
            _mark_outdated(p, 'error while fetching feed: %s' % str(nee))
            return p

        except Podcast.DoesNotExist:
            raise NoPodcastCreated(nee)

    assert parsed, 'fetch_feed must return something'
    p = Podcast.objects.get_or_create_for_url(podcast_url)
    episodes = _update_episodes(p, parsed.get('episodes', []))
    p.refresh_from_db()
    p.episode_count = Episode.objects.filter(podcast=p).count()
    p.save()
    max_episode_order = _order_episodes(p)
    _update_podcast(p, parsed, episodes, max_episode_order)
    return p


def verify_podcast_url(podcast_url):
    parsed = _fetch_feed(podcast_url)
    _validate_parsed(parsed)
    return True


def _fetch_feed(podcast_url):
    params = {
        'url': podcast_url,
        'process_text': 'markdown',
    }
    headers = {
        'Accept': 'application/json',
    }
    url = urljoin(settings.FEEDSERVICE_URL, 'parse')
    r = requests.get(url, params=params, headers=headers, timeout=10)

    if r.status_code != 200:
        logger.error('Feed-service status code for "%s" was %s', podcast_url,
                     r.status_code)
        return None

    try:
        return r.json()[0]
    except ValueError:
        logger.exception(
            'Feed-service error while parsing response for url "%s": %s',
            podcast_url, r.text,
        )
        raise


def _validate_parsed(parsed):
    """ validates the parsed results and raises an exception if invalid

    feedparser parses pretty much everything. We reject anything that
    doesn't look like a feed"""

    if not parsed or not parsed.get('episodes', []):
        raise NoEpisodesException('no episodes found')


def _update_podcast(podcast, parsed, episodes, max_episode_order):
    """ updates a podcast according to new parser results """

    # we need that later to decide if we can "bump" a category
    prev_latest_episode_timestamp = podcast.latest_episode_timestamp

    podcast.title = parsed.get('title') or podcast.title
    podcast.description = parsed.get('description') or podcast.description
    podcast.subtitle = parsed.get('subtitle') or podcast.subtitle
    podcast.link = parsed.get('link') or podcast.link
    podcast.logo_url = parsed.get('logo') or podcast.logo_url
    podcast.author = to_maxlength(Podcast, 'author', parsed.get('author') or
                                  podcast.author)
    podcast.language = to_maxlength(Podcast, 'language',
                                    parsed.get('language') or podcast.language)
    podcast.content_types = ','.join(parsed.get('content_types')) or \
                                     podcast.content_types
    #podcast.tags['feed'] = parsed.tags or podcast.tags.get('feed', [])
    podcast.common_episode_title = to_maxlength(
        Podcast,
        'common_episode_title',
        parsed.get('common_title') or podcast.common_episode_title)
    podcast.new_location = parsed.get('new_location') or podcast.new_location
    podcast.flattr_url = to_maxlength(Podcast, 'flattr_url',
                                      parsed.get('flattr') or
                                      podcast.flattr_url)
    podcast.hub = parsed.get('hub') or podcast.hub
    podcast.license = parsed.get('license') or podcast.license
    podcast.max_episode_order = max_episode_order

    podcast.add_missing_urls(parsed.get('urls', []))

    if podcast.new_location:
        try:
            new_podcast = Podcast.objects.get(urls__url=podcast.new_location)
            if new_podcast != podcast:
                _mark_outdated(podcast, 'redirected to different podcast')
                return
        except Podcast.DoesNotExist:
            podcast.set_url(podcast.new_location)

    # latest episode timestamp
    episodes = Episode.objects.filter(podcast=podcast,
                                      released__isnull=False)\
                              .order_by('released')

    podcast.update_interval = get_update_interval(episodes)

    latest_episode = episodes.last()
    if latest_episode:
        podcast.latest_episode_timestamp = latest_episode.released

    # podcast.episode_count is not update here on purpose. It is, instead,
    # continuously updated when creating new episodes in
    # EpisodeManager.get_or_create_for_url

    _update_categories(podcast, prev_latest_episode_timestamp)

    # try to download the logo and reset logo_url to None on http errors
    found = CoverArt.save_podcast_logo(podcast.logo_url)
    if not found:
        podcast.logo_url = None

    # The podcast is always saved (not just when there are changes) because
    # we need to record the last update
    logger.info('Saving podcast.')
    podcast.last_update = datetime.utcnow()
    podcast.save()

    try:
        subscribe_at_hub(podcast)
    except SubscriptionError as se:
        logger.warn('subscribing to hub failed: %s', str(se))

    assign_slug(podcast)
    assign_missing_episode_slugs(podcast)
    update_related_podcasts.delay(podcast)


def assign_slug(podcast):
    if podcast.slug:
        return

    for slug in PodcastSlugs(podcast):
        try:
            with transaction.atomic():
                podcast.add_slug(slug)
            break

        except:
            continue


def assign_missing_episode_slugs(podcast):
    common_title = podcast.get_common_episode_title()

    episodes = Episode.objects.filter(podcast=podcast, slugs__isnull=True)

    for episode in episodes:

        for slug in EpisodeSlugs(episode, common_title):
            try:
                with transaction.atomic():
                    episode.set_slug(slug)
                break

            except:
                continue


def _update_categories(podcast, prev_timestamp):
    """ checks some practical requirements and updates a category """

    max_timestamp = datetime.utcnow() + timedelta(days=1)

    # no episodes at all
    if not podcast.latest_episode_timestamp:
        return

    # no new episode
    if prev_timestamp and podcast.latest_episode_timestamp <= prev_timestamp:
        return

    # too far in the future
    if podcast.latest_episode_timestamp > max_timestamp:
        return

    # not enough subscribers
    if podcast.subscriber_count() < settings.MIN_SUBSCRIBERS_CATEGORY:
        return

    update_category(podcast)


def _update_episodes(podcast, parsed_episodes):

    pid = podcast.get_id()

    # list of (obj, fun) where fun is the function to update obj
    updated_episodes = []
    episodes_to_update = list(islice(parsed_episodes, 0, MAX_EPISODES_UPDATE))
    logger.info('Parsed %d (%d) episodes', len(parsed_episodes),
                len(episodes_to_update))

    logger.info('Updating %d episodes', len(episodes_to_update))
    for n, parsed in enumerate(episodes_to_update, 1):

        url = get_episode_url(parsed)
        if not url:
            logger.info('Skipping episode %d for missing URL', n)
            continue

        logger.info('Updating episode %d / %d', n, len(parsed_episodes))

        episode = Episode.objects.get_or_create_for_url(podcast, url)

        update_episode(parsed, episode, podcast)
        updated_episodes.append(episode)

    # and mark the remaining ones outdated
    current_episodes = Episode.objects.filter(podcast=podcast,
                                              outdated=False)[:500]
    outdated_episodes = set(current_episodes) - set(updated_episodes)

    logger.info('Marking %d episodes as outdated', len(outdated_episodes))
    for episode in outdated_episodes:
        mark_outdated(episode)


@transaction.atomic
def _order_episodes(podcast):
    """ Reorder the podcast's episode according to release timestamp

    Returns the highest order value (corresponding to the most recent
    episode) """

    num_episodes = podcast.episode_count
    if not num_episodes:
        return 0

    episodes = podcast.episode_set.all().extra(select={
        'has_released': 'released IS NOT NULL',
        })\
        .order_by('-has_released', '-released', 'pk')\
        .only('pk')

    for n, episode in enumerate(episodes.iterator(), 1):
        # assign ``order`` from higher (most recent) to 0 (oldest)
        # None means "unknown"
        new_order = num_episodes - n

        # optimize for new episodes that are newer than all existing
        if episode.order == new_order:
            continue

        logger.info('Updating order from {} to {}'.format(episode.order,
                                                          new_order))
        episode.order = new_order
        episode.save()

    return num_episodes - 1


def _mark_outdated(podcast, msg=''):
    logger.info('marking podcast outdated: %s', msg)
    podcast.outdated = True
    podcast.last_update = datetime.utcnow()
    podcast.save()
    _update_episodes(podcast, [])


def get_episode_url(parsed_episode):
    """ returns the URL of a parsed episode """
    for f in parsed_episode.get('files', []):
        if f.get('urls', []):
            return f['urls'][0]
    return None


def update_episode(parsed_episode, episode, podcast):
    """ updates "episode" with the data from "parsed_episode" """

    # TODO: check if there have been any changes, to avoid unnecessary updates
    episode.guid = to_maxlength(Episode, 'guid', parsed_episode.get('guid') or
                                episode.guid)
    episode.description = parsed_episode.get('description') or \
        episode.description
    episode.subtitle = parsed_episode.get('subtitle') or episode.subtitle
    episode.content = parsed_episode.get('content') or \
        parsed_episode.get('description') or episode.content
    episode.link = to_maxlength(Episode, 'link',
                                parsed_episode.get('link') or episode.link)
    episode.released = datetime.utcfromtimestamp(
        parsed_episode.get('released')) if parsed_episode.get('released') \
        else episode.released
    episode.author = to_maxlength(Episode, 'author',
                                  parsed_episode.get('author') or
                                  episode.author)
    episode.duration = parsed_episode.get('duration') or episode.duration
    episode.filesize = parsed_episode['files'][0]['filesize']
    episode.language = parsed_episode.get('language') or \
        episode.language or podcast.language
    episode.mimetypes = ','.join(list(set(
        filter(None, [f['mimetype'] for f in parsed_episode.get('files', [])])
    )))
    episode.flattr_url = to_maxlength(Episode, 'flattr_url',
                                      parsed_episode.get('flattr') or
                                      episode.flattr_url)
    episode.license = parsed_episode.get('license') or episode.license

    episode.title = to_maxlength(Episode, 'title',
                                 parsed_episode.get('title') or
                                 episode.title or
                                 file_basename_no_extension(episode.url))

    episode.last_update = datetime.utcnow()
    episode.save()

    parsed_urls = list(chain.from_iterable(
        f.get('urls', []) for f in parsed_episode.get('files', [])))
    episode.add_missing_urls(parsed_urls)


def mark_outdated(obj):
    """ marks obj outdated if its not already """
    if obj.outdated:
        return None

    obj.outdated = True
    obj.last_update = datetime.utcnow()
    obj.save()


def get_update_interval(episodes):
    """ calculates the avg interval between new episodes """

    count = len(episodes)
    if not count:
        logger.info('no episodes, using default interval of %dh',
                    DEFAULT_UPDATE_INTERVAL)
        return DEFAULT_UPDATE_INTERVAL

    earliest = episodes[0]
    now = datetime.utcnow()

    timespan_s = (now - earliest.released).total_seconds()
    timespan_h = timespan_s / 60 / 60

    interval = int(timespan_h / count)
    logger.info('%d episodes in %d days => %dh interval', count,
                timespan_h / 24, interval)

    # place interval between {MIN,MAX}_UPDATE_INTERVAL
    interval = max(interval, MIN_UPDATE_INTERVAL)
    interval = min(interval, MAX_UPDATE_INTERVAL)

    return interval


def file_basename_no_extension(filename):
    """ Returns filename without extension

    >>> file_basename_no_extension('/home/me/file.txt')
    'file'

    >>> file_basename_no_extension('file')
    'file'
    """
    base = os.path.basename(filename)
    name, extension = os.path.splitext(base)
    return name
