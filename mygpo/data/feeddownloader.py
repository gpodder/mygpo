#!/usr/bin/python
# -*- coding: utf-8 -*-

import os.path
import urllib.request
import urllib.error
from urllib.parse import urljoin
import hashlib
from datetime import datetime, timedelta
from itertools import chain, islice
import requests

from django.db import transaction
from django.conf import settings

from mygpo.podcasts.models import Podcast, Episode
from mygpo.core.slugs import PodcastSlugs, EpisodeSlugs
from mygpo.podcasts.models import (
    DEFAULT_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
    MAX_UPDATE_INTERVAL,
)
from mygpo.utils import to_maxlength
from mygpo.web.logo import CoverArt
from mygpo.data.podcast import subscribe_at_hub
from mygpo.data.tasks import update_related_podcasts
from mygpo.pubsub.models import SubscriptionError
from mygpo.directory.tags import update_category
from mygpo.search import get_index_fields

from . import models

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
        if not podcast_url:
            logger.warn('Podcast URL empty, skipping')
            continue

        try:
            updater = PodcastUpdater(podcast_url)
            yield updater.update_podcast()

        except NoPodcastCreated as npc:
            logger.info('No podcast created: %s', npc)

        except GeneratorExit:
            pass

        except:
            logger.exception('Error while updating podcast "%s"', podcast_url)
            raise


class PodcastUpdater(object):
    """ Updates the podcast specified by the podcast_url """

    def __init__(self, podcast_url):
        self.podcast_url = podcast_url

    def update_podcast(self):
        """ Update the podcast """

        with models.PodcastUpdateResult(podcast_url=self.podcast_url) as res:

            parsed, podcast, created = self.parse_feed()

            if not podcast:
                res.podcast_created = False
                res.error_message = '"{}" could not be parsed'.format(self.podcast_url)

                return

            res.podcast = podcast
            res.podcast_created = created

            res.episodes_added = 0
            episode_updater = MultiEpisodeUpdater(podcast, res)

            if not parsed:
                # if it exists already, we mark it as outdated
                self._mark_outdated(
                    podcast, 'error while fetching feed', episode_updater
                )
                return

            episode_updater.update_episodes(parsed.get('episodes', []))

            podcast.refresh_from_db()
            podcast.episode_count = episode_updater.count_episodes()
            podcast.save()

            episode_updater.order_episodes()

            self._update_podcast(podcast, parsed, episode_updater, res)

        return podcast

    def parse_feed(self):
        try:
            parsed = self._fetch_feed()
            self._validate_parsed(parsed)

        except (requests.exceptions.RequestException, NoEpisodesException) as ex:
            logging.exception('Error while fetching/parsing feed')

            # if we fail to parse the URL, we don't even create the
            # podcast object
            try:
                p = Podcast.objects.get(urls__url=self.podcast_url)
                return (None, p, False)

            except Podcast.DoesNotExist as pdne:
                raise NoPodcastCreated(ex) from pdne

        # Parsing went well, get podcast
        podcast, created = Podcast.objects.get_or_create_for_url(self.podcast_url)

        return (parsed, podcast, created)

    def _fetch_feed(self):
        params = {'url': self.podcast_url, 'process_text': 'markdown'}
        headers = {'Accept': 'application/json'}
        url = urljoin(settings.FEEDSERVICE_URL, 'parse')
        r = requests.get(url, params=params, headers=headers, timeout=30)

        if r.status_code != 200:
            logger.error(
                'Feed-service status code for "{}" was {}'.format(url, r.status_code)
            )
            return None

        try:
            return r.json()[0]
        except ValueError:
            logger.exception(
                'Feed-service error while parsing response for url "%s": %s',
                podcast_url,
                r.text,
            )
            raise

    def _validate_parsed(self, parsed):
        """ validates the parsed results and raises an exception if invalid

        feedparser parses pretty much everything. We reject anything that
        doesn't look like a feed"""

        if not parsed or not parsed.get('episodes', []):
            raise NoEpisodesException('no episodes found')

    def _update_podcast(self, podcast, parsed, episode_updater, update_result):
        """ updates a podcast according to new parser results """

        # we need that later to decide if we can "bump" a category
        prev_latest_episode_timestamp = podcast.latest_episode_timestamp

        # will later be used to see whether the index is outdated
        old_index_fields = get_index_fields(podcast)

        podcast.title = parsed.get('title') or podcast.title
        podcast.description = parsed.get('description') or podcast.description
        podcast.subtitle = parsed.get('subtitle') or podcast.subtitle
        podcast.link = parsed.get('link') or podcast.link
        podcast.logo_url = parsed.get('logo') or podcast.logo_url

        podcast.author = to_maxlength(
            Podcast, 'author', parsed.get('author') or podcast.author
        )

        podcast.language = to_maxlength(
            Podcast, 'language', parsed.get('language') or podcast.language
        )

        podcast.content_types = (
            ','.join(parsed.get('content_types')) or podcast.content_types
        )

        # podcast.tags['feed'] = parsed.tags or podcast.tags.get('feed', [])

        podcast.common_episode_title = to_maxlength(
            Podcast,
            'common_episode_title',
            parsed.get('common_title') or podcast.common_episode_title,
        )

        podcast.new_location = parsed.get('new_location') or podcast.new_location
        podcast.flattr_url = to_maxlength(
            Podcast, 'flattr_url', parsed.get('flattr') or podcast.flattr_url
        )
        podcast.hub = parsed.get('hub') or podcast.hub
        podcast.license = parsed.get('license') or podcast.license
        podcast.max_episode_order = episode_updater.max_episode_order

        podcast.add_missing_urls(parsed.get('urls', []))

        if podcast.new_location:
            try:
                new_podcast = Podcast.objects.get(urls__url=podcast.new_location)

                if new_podcast != podcast:
                    self._mark_outdated(
                        podcast, 'redirected to different podcast', episode_updater
                    )
                    return
            except Podcast.DoesNotExist:
                podcast.set_url(podcast.new_location)

        # latest episode timestamp
        episodes = Episode.objects.filter(
            podcast=podcast, released__isnull=False
        ).order_by('released')

        # Determine update interval

        # Update interval is based on intervals between episodes
        podcast.update_interval = episode_updater.get_update_interval(episodes)

        # factor is increased / decreased depending on whether the latest
        # update has returned episodes
        if update_result.episodes_added == 0:  # no episodes, incr factor
            newfactor = podcast.update_interval_factor * 1.2
            podcast.update_interval_factor = min(1000, newfactor)  # never above 1000
        elif update_result.episodes_added > 1:  # new episodes, decr factor
            newfactor = podcast.update_interval_factor / 1.2
            podcast.update_interval_factor = max(1, newfactor)  # never below 1

        latest_episode = episodes.last()
        if latest_episode:
            podcast.latest_episode_timestamp = latest_episode.released

        # podcast.episode_count is not update here on purpose. It is, instead,
        # continuously updated when creating new episodes in
        # EpisodeManager.get_or_create_for_url

        self._update_categories(podcast, prev_latest_episode_timestamp)

        # try to download the logo and reset logo_url to None on http errors
        found = CoverArt.save_podcast_logo(podcast.logo_url)
        if not found:
            podcast.logo_url = None

        # check if search index should be considered out of date
        new_index_fields = get_index_fields(podcast)
        if list(old_index_fields.items()) != list(new_index_fields.items()):
            podcast.search_index_uptodate = False

        # The podcast is always saved (not just when there are changes) because
        # we need to record the last update
        logger.info('Saving podcast.')
        podcast.last_update = datetime.utcnow()
        podcast.save()

        try:
            subscribe_at_hub(podcast)
        except SubscriptionError as se:
            logger.warn('subscribing to hub failed: %s', str(se))

        self.assign_slug(podcast)
        episode_updater.assign_missing_episode_slugs()
        update_related_podcasts.delay(podcast.pk)

    def assign_slug(self, podcast):
        if podcast.slug:
            return

        for slug in PodcastSlugs(podcast):
            try:
                with transaction.atomic():
                    podcast.add_slug(slug)
                break

            except:
                continue

    def _update_categories(self, podcast, prev_timestamp):
        """ checks some practical requirements and updates a category """

        max_timestamp = datetime.utcnow() + timedelta(days=1)

        # no episodes at all
        if not podcast.latest_episode_timestamp:
            return

        # no new episode
        if prev_timestamp and (podcast.latest_episode_timestamp <= prev_timestamp):
            return

        # too far in the future
        if podcast.latest_episode_timestamp > max_timestamp:
            return

        # not enough subscribers
        if podcast.subscriber_count() < settings.MIN_SUBSCRIBERS_CATEGORY:
            return

        update_category(podcast)

    def _mark_outdated(self, podcast, msg, episode_updater):
        logger.info('marking podcast outdated: %s', msg)
        podcast.outdated = True
        podcast.last_update = datetime.utcnow()
        podcast.save()
        episode_updater.update_episodes([])


class MultiEpisodeUpdater(object):
    def __init__(self, podcast, update_result):
        self.podcast = podcast
        self.update_result = update_result
        self.updated_episodes = []
        self.max_episode_order = None

    def update_episodes(self, parsed_episodes):

        pid = self.podcast.get_id()

        episodes_to_update = list(islice(parsed_episodes, 0, MAX_EPISODES_UPDATE))
        logger.info(
            'Parsed %d (%d) episodes', len(parsed_episodes), len(episodes_to_update)
        )

        logger.info('Updating %d episodes', len(episodes_to_update))
        for n, parsed in enumerate(episodes_to_update, 1):

            url = self.get_episode_url(parsed)
            if not url:
                logger.info('Skipping episode %d for missing URL', n)
                continue

            logger.info('Updating episode %d / %d', n, len(parsed_episodes))

            episode, created = Episode.objects.get_or_create_for_url(self.podcast, url)

            if created:
                self.update_result.episodes_added += 1

            updater = EpisodeUpdater(episode, self.podcast)
            updater.update_episode(parsed)

            self.updated_episodes.append(episode)

        # and mark the remaining ones outdated
        current_episodes = Episode.objects.filter(podcast=self.podcast, outdated=False)[
            :500
        ]
        outdated_episodes = set(current_episodes) - set(self.updated_episodes)

        logger.info('Marking %d episodes as outdated', len(outdated_episodes))
        for episode in outdated_episodes:
            updater = EpisodeUpdater(episode, self.podcast)
            updater.mark_outdated()

    @transaction.atomic
    def order_episodes(self):
        """ Reorder the podcast's episode according to release timestamp

        Returns the highest order value (corresponding to the most recent
        episode) """

        num_episodes = self.podcast.episode_count
        if not num_episodes:
            return 0

        episodes = (
            self.podcast.episode_set.all()
            .extra(select={'has_released': 'released IS NOT NULL'})
            .order_by('-has_released', '-released', 'pk')
            .only('pk')
        )

        for n, episode in enumerate(episodes.iterator(), 1):
            # assign ``order`` from higher (most recent) to 0 (oldest)
            # None means "unknown"
            new_order = num_episodes - n

            # optimize for new episodes that are newer than all existing
            if episode.order == new_order:
                continue

            logger.info('Updating order from {} to {}'.format(episode.order, new_order))
            episode.order = new_order
            episode.save()

        self.max_episode_order = num_episodes - 1

    def get_episode_url(self, parsed_episode):
        """ returns the URL of a parsed episode """
        for f in parsed_episode.get('files', []):
            if f.get('urls', []):
                return f['urls'][0]
        return None

    def count_episodes(self):
        return Episode.objects.filter(podcast=self.podcast).count()

    def get_update_interval(self, episodes):
        """ calculates the avg interval between new episodes """

        count = episodes.count()
        if not count:
            logger.info(
                'no episodes, using default interval of %dh', DEFAULT_UPDATE_INTERVAL
            )
            return DEFAULT_UPDATE_INTERVAL

        earliest = episodes.first()
        now = datetime.utcnow()

        timespan_s = (now - earliest.released).total_seconds()
        timespan_h = timespan_s / 60 / 60

        interval = int(timespan_h / count)
        logger.info(
            '%d episodes in %d days => %dh interval', count, timespan_h / 24, interval
        )

        # place interval between {MIN,MAX}_UPDATE_INTERVAL
        interval = max(interval, MIN_UPDATE_INTERVAL)
        interval = min(interval, MAX_UPDATE_INTERVAL)

        return interval

    def assign_missing_episode_slugs(self):
        common_title = self.podcast.get_common_episode_title()

        episodes = Episode.objects.filter(podcast=self.podcast, slugs__isnull=True)

        for episode in episodes:

            for slug in EpisodeSlugs(episode, common_title):
                try:
                    with transaction.atomic():
                        episode.set_slug(slug)
                    break

                except:
                    continue


class EpisodeUpdater(object):
    """ Updates an individual episode """

    def __init__(self, episode, podcast):
        self.episode = episode
        self.podcast = podcast

    def update_episode(self, parsed_episode):
        """ updates "episode" with the data from "parsed_episode" """

        # TODO: check if there have been any changes, to
        # avoid unnecessary updates
        self.episode.guid = to_maxlength(
            Episode, 'guid', parsed_episode.get('guid') or self.episode.guid
        )

        self.episode.description = (
            parsed_episode.get('description') or self.episode.description
        )

        self.episode.subtitle = parsed_episode.get('subtitle') or self.episode.subtitle

        self.episode.content = (
            parsed_episode.get('content')
            or parsed_episode.get('description')
            or self.episode.content
        )

        self.episode.link = to_maxlength(
            Episode, 'link', parsed_episode.get('link') or self.episode.link
        )

        self.episode.released = (
            datetime.utcfromtimestamp(parsed_episode.get('released'))
            if parsed_episode.get('released')
            else self.episode.released
        )

        self.episode.author = to_maxlength(
            Episode, 'author', parsed_episode.get('author') or self.episode.author
        )

        self.episode.duration = parsed_episode.get('duration') or self.episode.duration

        self.episode.filesize = parsed_episode['files'][0]['filesize']

        self.episode.language = (
            parsed_episode.get('language')
            or self.episode.language
            or self.podcast.language
        )

        mimetypes = [f['mimetype'] for f in parsed_episode.get('files', [])]
        self.episode.mimetypes = ','.join(list(set(filter(None, mimetypes))))

        self.episode.flattr_url = to_maxlength(
            Episode,
            'flattr_url',
            parsed_episode.get('flattr') or self.episode.flattr_url,
        )

        self.episode.license = parsed_episode.get('license') or self.episode.license

        self.episode.title = to_maxlength(
            Episode,
            'title',
            parsed_episode.get('title')
            or self.episode.title
            or file_basename_no_extension(self.episode.url),
        )

        self.episode.last_update = datetime.utcnow()
        self.episode.save()

        parsed_urls = list(
            chain.from_iterable(
                f.get('urls', []) for f in parsed_episode.get('files', [])
            )
        )
        self.episode.add_missing_urls(parsed_urls)

    def mark_outdated(self):
        """ marks the episode outdated if its not already """
        if self.episode.outdated:
            return None

        self.episode.outdated = True
        self.episode.last_update = datetime.utcnow()
        self.episode.save()


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


def verify_podcast_url(url):
    updater = PodcastUpdater(url)
    parsed = updater._fetch_feed()
    updater._validate_parsed(parsed)
    return True
