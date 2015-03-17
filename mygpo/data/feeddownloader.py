#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This file is part of my.gpodder.org.
#
# my.gpodder.org is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# my.gpodder.org is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public
# License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with my.gpodder.org. If not, see <http://www.gnu.org/licenses/>.
#

import os.path
import urllib2
import httplib
import hashlib
from datetime import datetime
from itertools import chain, islice
import socket

from django.db import transaction
from django.conf import settings

from mygpo.podcasts.models import Podcast, URL, Slug, Episode
from mygpo.core.slugs import assign_missing_episode_slugs, PodcastSlug
from mygpo.podcasts.models import DEFAULT_UPDATE_INTERVAL, \
    MIN_UPDATE_INTERVAL, MAX_UPDATE_INTERVAL
from feedservice.parse import parse_feed, FetchFeedException
from feedservice.parse.text import ConvertMarkdown
from feedservice.parse.models import ParserException
from feedservice.parse.vimeo import VimeoError
from mygpo.utils import file_hash, to_maxlength
from mygpo.web.logo import CoverArt
from mygpo.data.podcast import subscribe_at_hub
from mygpo.data.tasks import update_related_podcasts
from mygpo.pubsub.models import SubscriptionError
from mygpo.directory.tags import update_category

import logging
logger = logging.getLogger(__name__)

MAX_EPISODES_UPDATE=200

class NoPodcastCreated(Exception):
    """ raised when no podcast obj was created for a new URL """


class NoEpisodesException(Exception):
    """ raised when parsing something that doesn't contain any episodes """


class PodcastUpdater(object):
    """ Updates a number of podcasts with data from their feeds """

    def update_queue(self, queue):
        """ Fetch data for the URLs supplied as the queue iterable """

        for n, podcast_url in enumerate(queue, 1):
            logger.info('Update %d - %s', n, podcast_url)
            try:
                yield self.update(podcast_url)

            except NoPodcastCreated as npc:
                logger.info('No podcast created: %s', npc)

            except:
                logger.exception('Error while updating podcast "%s"',
                                 podcast_url)
                raise


    def update(self, podcast_url):
        """ Update the podcast for the supplied URL """

        try:
            parsed = self._fetch_feed(podcast_url)
            self._validate_parsed(parsed)

        except (ParserException, FetchFeedException, NoEpisodesException,
                VimeoError, ValueError, socket.error, urllib2.HTTPError) as ex:
            #TODO: catch valueError (for invalid Ipv6 in feedservice)

            if isinstance(ex, VimeoError):
                logger.exception('Problem when updating Vimeo feed %s',
                                 podcast_url)

            # if we fail to parse the URL, we don't even create the
            # podcast object
            try:
                p = Podcast.objects.get(urls__url=podcast_url)
                # if it exists already, we mark it as outdated
                self._mark_outdated(p, 'error while fetching feed: %s' %
                    str(ex))
                return p

            except Podcast.DoesNotExist:
                raise NoPodcastCreated(ex)

        assert parsed, 'fetch_feed must return something'
        p = Podcast.objects.get_or_create_for_url(podcast_url)
        episodes = self._update_episodes(p, parsed.episodes)
        max_episode_order = self._order_episodes(p)
        self._update_podcast(p, parsed, episodes, max_episode_order)
        return p


    def verify_podcast_url(self, podcast_url):
        parsed = self._fetch_feed(podcast_url)
        self._validate_parsed(parsed)
        return True


    def _fetch_feed(self, podcast_url):
        import socket
        t = socket.getdefaulttimeout()
        socket.setdefaulttimeout(10)
        return parse_feed(podcast_url, text_processor=ConvertMarkdown())
        socket.setdefaulttimeout(t)



    def _validate_parsed(self, parsed):
        """ validates the parsed results and raises an exception if invalid

        feedparser parses pretty much everything. We reject anything that
        doesn't look like a feed"""

        if not parsed or not parsed.episodes:
            raise NoEpisodesException('no episodes found')


    def _update_podcast(self, podcast, parsed, episodes, max_episode_order):
        """ updates a podcast according to new parser results """

        # we need that later to decide if we can "bump" a category
        prev_latest_episode_timestamp = podcast.latest_episode_timestamp

        podcast.title = parsed.title or podcast.title
        podcast.description = parsed.description or podcast.description
        podcast.subtitle = parsed.subtitle or podcast.subtitle
        podcast.link = parsed.link or podcast.link
        podcast.logo_url = parsed.logo or podcast.logo_url
        podcast.author = to_maxlength(Podcast, 'author', parsed.author or podcast.author)
        podcast.language = to_maxlength(Podcast, 'language', parsed.language or podcast.language)
        podcast.content_types = ','.join(parsed.content_types) or podcast.content_types
#podcast.tags['feed'] = parsed.tags or podcast.tags.get('feed', [])
        podcast.common_episode_title = to_maxlength(Podcast,
            'common_episode_title',
            parsed.common_title or podcast.common_episode_title)
        podcast.new_location = parsed.new_location or podcast.new_location
        podcast.flattr_url = to_maxlength(Podcast, 'flattr_url',
                                          parsed.flattr or podcast.flattr_url)
        podcast.hub = parsed.hub or podcast.hub
        podcast.license = parsed.license or podcast.license
        podcast.max_episode_order = max_episode_order

        podcast.add_missing_urls(parsed.urls)

        if podcast.new_location:
            try:
                new_podcast = Podcast.objects.get(urls__url=podcast.new_location)
                if new_podcast != podcast:
                    self._mark_outdated(podcast, 'redirected to different podcast')
                    return
            except Podcast.DoesNotExist:
                podcast.set_url(podcast.new_location)


        # latest episode timestamp
        episodes = Episode.objects.filter(podcast=podcast, released__isnull=False).order_by('released')

        podcast.update_interval = get_update_interval(episodes)

        latest_episode = episodes.last()
        if latest_episode:
            podcast.latest_episode_timestamp = latest_episode.released

        # podcast.episode_count is not update here on purpose. It is, instead,
        # continuously updated when creating new episodes in
        # EpisodeManager.get_or_create_for_url

        self._update_categories(podcast, prev_latest_episode_timestamp)

        # try to download the logo and reset logo_url to None on http errors
        found = self._save_podcast_logo(podcast.logo_url)
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


        if not podcast.slug:
            slug = PodcastSlug(podcast).get_slug()
            if slug:
                podcast.add_slug(slug)

        assign_missing_episode_slugs(podcast)
        update_related_podcasts.delay(podcast)


    def _update_categories(self, podcast, prev_timestamp):
        """ checks some practical requirements and updates a category """

        from datetime import timedelta

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


    def _update_episodes(self, podcast, parsed_episodes):

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
    def _order_episodes(self, podcast):
        """ Reorder the podcast's episode according to release timestamp

        Returns the highest order value (corresponding to the most recent
        episode) """

        num_episodes = podcast.episode_set.count()
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

        return num_episodes -1

    def _save_podcast_logo(self, cover_art):
        if not cover_art:
            return

        try:
            image_sha1 = hashlib.sha1(cover_art).hexdigest()
            prefix = CoverArt.get_prefix(image_sha1)

            filename = CoverArt.get_original(prefix, image_sha1)
            dirname = CoverArt.get_dir(filename)

            # get hash of existing file
            if os.path.exists(filename):
                with open(filename) as f:
                    old_hash = file_hash(f).digest()
            else:
                old_hash = ''

            logger.info('Logo %s', cover_art)

            # save new cover art
            with open(filename, 'w') as fp:
                fp.write(urllib2.urlopen(cover_art).read())

            # get hash of new file
            with open(filename) as f:
                new_hash = file_hash(f).digest()

            # remove thumbnails if cover changed
            if old_hash != new_hash:
                thumbnails = CoverArt.get_existing_thumbnails(prefix, filename)
                logger.info('Removing %d thumbnails', len(thumbnails))
                for f in thumbnails:
                    os.unlink(f)

            return cover_art

        except (urllib2.HTTPError, urllib2.URLError, ValueError,
                httplib.BadStatusLine, socket.error, IOError) as e:
            logger.warn('Exception while updating podcast logo: %s', str(e))


    def _mark_outdated(self, podcast, msg=''):
        logger.info('marking podcast outdated: %s', msg)
        podcast.outdated = True
        podcast.last_update = datetime.utcnow()
        podcast.save()
        self._update_episodes(podcast, [])


def get_episode_url(parsed_episode):
    """ returns the URL of a parsed episode """
    for f in parsed_episode.files:
        if f.urls:
            return f.urls[0]
    return None


def update_episode(parsed_episode, episode, podcast):
    """ updates "episode" with the data from "parsed_episode" """

    # TODO: check if there have been any changes, to avoid unnecessary updates
    episode.guid = to_maxlength(Episode, 'guid', parsed_episode.guid or episode.guid)
    episode.description = parsed_episode.description or episode.description
    episode.subtitle = parsed_episode.subtitle or episode.subtitle
    episode.content = parsed_episode.content or parsed_episode.description or episode.content
    episode.link = to_maxlength(Episode, 'link',
                                parsed_episode.link or episode.link)
    episode.released = datetime.utcfromtimestamp(parsed_episode.released) if parsed_episode.released else episode.released
    episode.author = to_maxlength(Episode, 'author', parsed_episode.author or episode.author)
    episode.duration = parsed_episode.duration or episode.duration
    episode.filesize = parsed_episode.files[0].filesize
    episode.language = parsed_episode.language or episode.language or \
                                                  podcast.language
    episode.mimetypes = ','.join(list(set(filter(None, [f.mimetype for f in parsed_episode.files]))))
    episode.flattr_url = to_maxlength(Episode, 'flattr_url',
                                      parsed_episode.flattr or
                                      episode.flattr_url)
    episode.license = parsed_episode.license or episode.license

    episode.title = to_maxlength(Episode, 'title',
                                 parsed_episode.title or episode.title or
                                 file_basename_no_extension(episode.url))

    episode.last_update = datetime.utcnow()
    episode.save()

    parsed_urls = list(chain.from_iterable(f.urls for f in parsed_episode.files))
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
