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

import copy
import os.path
import urllib2
import httplib
import hashlib
from datetime import datetime
from itertools import chain

from django.conf import settings

from mygpo.core.slugs import assign_missing_episode_slugs, assign_slug, \
         PodcastSlug
from mygpo.core.models import DEFAULT_UPDATE_INTERVAL, MIN_UPDATE_INTERVAL, \
    MAX_UPDATE_INTERVAL
from feedservice.parse import parse_feed, FetchFeedException
from feedservice.parse.text import ConvertMarkdown
from feedservice.parse.models import ParserException
from mygpo.utils import file_hash, deep_eq
from mygpo.web.logo import CoverArt
from mygpo.data.podcast import subscribe_at_hub
from mygpo.db.couchdb.episode import episode_for_podcast_id_url, \
         episodes_for_podcast_current, episode_count_for_podcast
from mygpo.db.couchdb.podcast import podcast_for_url, reload_podcast
from mygpo.directory.tags import update_category
from mygpo.decorators import repeat_on_conflict
from mygpo.db.couchdb import get_main_database, bulk_save_retry

import logging
logger = logging.getLogger(__name__)


class NoPodcastCreated(Exception):
    """ raised when no podcast obj was created for a new URL """


class NoEpisodesException(Exception):
    """ raised when parsing something that doesn't contain any episodes """


class PodcastUpdater(object):
    """ Updates a number of podcasts with data from their feeds """

    def __init__(self):
        """ Queue is an iterable of podcast objects """
        self.db = get_main_database()


    def update_queue(self, queue):
        """ Fetch data for the URLs supplied as the queue iterable """

        for n, podcast_url in enumerate(queue, 1):
            logger.info('Update %d - %s', n, podcast_url)
            try:
                yield self.update(podcast_url)

            except NoPodcastCreated as npc:
                logger.info('No podcast created: %s', npc)


    def update(self, podcast_url):
        """ Update the podcast for the supplied URL """

        try:
            parsed = self._fetch_feed(podcast_url)
            self._validate_parsed(parsed)

        except (ParserException, FetchFeedException, NoEpisodesException) as ex:

            # if we fail to parse the URL, we don't even create the
            # podcast object
            p = podcast_for_url(podcast_url, create=False)
            if p:
                # if it exists already, we mark it as outdated
                self._mark_outdated(p, 'error while fetching feed: %s' %
                    str(ex))
                return p

            else:
                raise NoPodcastCreated(ex)

        assert parsed, 'fetch_feed must return something'
        p = podcast_for_url(podcast_url, create=True)
        episodes = self._update_episodes(p, parsed.episodes)
        self._update_podcast(p, parsed, episodes)
        return p


    def verify_podcast_url(self, podcast_url):
        parsed = self._fetch_feed(podcast_url)
        self._validate_parsed(parsed)
        return True


    def _fetch_feed(self, podcast_url):
        return parse_feed(podcast_url, text_processor=ConvertMarkdown())



    def _validate_parsed(self, parsed):
        """ validates the parsed results and raises an exception if invalid

        feedparser parses pretty much everything. We reject anything that
        doesn't look like a feed"""

        if not parsed or not parsed.episodes:
            raise NoEpisodesException('no episodes found')


    @repeat_on_conflict(['podcast'], reload_f=reload_podcast)
    def _update_podcast(self, podcast, parsed, episodes):
        """ updates a podcast according to new parser results """

        # we need that later to decide if we can "bump" a category
        prev_latest_episode_timestamp = podcast.latest_episode_timestamp

        old_json = copy.deepcopy(podcast.to_json())

        podcast.title = parsed.title or podcast.title
        podcast.urls = list(set(podcast.urls + parsed.urls))
        podcast.description = parsed.description or podcast.description
        podcast.subtitle = parsed.subtitle or podcast.subtitle
        podcast.link = parsed.link or podcast.link
        podcast.logo_url = parsed.logo or podcast.logo_url
        podcast.author = parsed.author or podcast.author
        podcast.language = parsed.language or podcast.language
        podcast.content_types = parsed.content_types or podcast.content_types
        podcast.tags['feed'] = parsed.tags or podcast.tags.get('feed', [])
        podcast.common_episode_title = parsed.common_title or podcast.common_episode_title
        podcast.new_location = parsed.new_location or podcast.new_location
        podcast.flattr_url = parsed.flattr or podcast.flattr_url
        podcast.hub = parsed.hub or podcast.hub
        podcast.license = parsed.license or podcast.license


        if podcast.new_location:
            new_podcast = podcast_for_url(podcast.new_location)
            if new_podcast != podcast:
                self._mark_outdated(podcast, 'redirected to different podcast')
                return

            elif not new_podcast:
                podcast.urls.insert(0, podcast.new_location)


        logger.info('Retrieved %d episodes in total', len(episodes))

        # latest episode timestamp
        eps = filter(lambda e: bool(e.released), episodes)
        eps = sorted(eps, key=lambda e: e.released)

        podcast.update_interval = get_update_interval(eps)

        if eps:
            podcast.latest_episode_timestamp = eps[-1].released

        podcast.episode_count = episode_count_for_podcast(podcast)


        self._update_categories(podcast, prev_latest_episode_timestamp)

        # try to download the logo and reset logo_url to None on http errors
        found = self._save_podcast_logo(podcast.logo_url)
        if not found:
            podcast.logo_url = None

        if not deep_eq(old_json, podcast.to_json()):
            logger.info('Saving podcast.')
            podcast.last_update = datetime.utcnow()
            podcast.save()


        subscribe_at_hub(podcast)

        assign_slug(podcast, PodcastSlug)
        assign_missing_episode_slugs(podcast)


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
        changes = []
        logger.info('Parsed %d episodes', len(parsed_episodes))

        for n, parsed in enumerate(parsed_episodes, 1):

            url = get_episode_url(parsed)
            if not url:
                logger.info('Skipping episode %d for missing URL', n)
                continue

            logger.info('Updating episode %d / %d', n, len(parsed_episodes))
            episode = episode_for_podcast_id_url(pid, url, create=True)

            update_episode = get_episode_update_function(parsed, episode,
                                                         podcast)
            changes.append((episode, update_episode))

        # determine which episodes have been found
        updated_episodes = [e for (e, f) in changes]
        logging.info('Updating %d episodes with new data', len(updated_episodes))

        # and mark the remaining ones outdated
        current_episodes = set(episodes_for_podcast_current(podcast, limit=100))
        outdated_episodes = current_episodes - set(updated_episodes)
        logging.info('Marking %d episodes as outdated', len(outdated_episodes))
        changes.extend((e, mark_outdated) for e in outdated_episodes)

        logging.info('Saving %d changes', len(changes))
        bulk_save_retry(changes, self.db)

        return updated_episodes


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
                httplib.BadStatusLine) as e:
            logger.warn('Exception while updating podcast: %s', str(e))


    @repeat_on_conflict(['podcast'], reload_f=reload_podcast)
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


def get_episode_update_function(parsed_episode, episode, podcast):
    """ returns an update function that can be passed to bulk_save_retry """

    def update_episode(episode):
        """ updates "episode" with the data from "parsed_episode" """

        # copy the json so we can determine if there have been any changes
        old_json = copy.deepcopy(episode.to_json())

        episode.guid = parsed_episode.guid or episode.guid
        episode.title = parsed_episode.title or episode.title
        episode.description = parsed_episode.description or episode.description
        episode.subtitle = parsed_episode.subtitle or episode.subtitle
        episode.content = parsed_episode.content or parsed_episode.description or episode.content
        episode.link = parsed_episode.link or episode.link
        episode.released = datetime.utcfromtimestamp(parsed_episode.released) if parsed_episode.released else episode.released
        episode.author = parsed_episode.author or episode.author
        episode.duration = parsed_episode.duration or episode.duration
        episode.filesize = parsed_episode.files[0].filesize
        episode.language = parsed_episode.language or episode.language or \
                                                      podcast.language
        episode.mimetypes = list(set(filter(None, [f.mimetype for f in parsed_episode.files])))
        episode.flattr_url = parsed_episode.flattr or episode.flattr_url
        episode.license = parsed_episode.license or episode.license

        urls = list(chain.from_iterable(f.urls for f in parsed_episode.files))
        episode.urls = sorted(set(episode.urls + urls), key=len)

        # if nothing changed we return None to indicate no required action
        if deep_eq(old_json, episode.to_json()):
            return None

        # set the last_update only if there have been changed above
        episode.last_update = datetime.utcnow()
        return episode

    return update_episode

def mark_outdated(obj):
    """ marks obj outdated if its not already """
    if obj.outdated:
        return None

    obj.outdated = True
    obj.last_update = datetime.utcnow()
    return obj


def get_update_interval(episodes):
    """ calculates the avg interval between new episodes """

    count = len(episodes)
    if count <= 1:
        logger.info('%d episodes, using default interval of %dh',
            count, DEFAULT_UPDATE_INTERVAL)
        return DEFAULT_UPDATE_INTERVAL

    earliest = episodes[0]
    latest   = episodes[-1]

    timespan_s = (latest.released - earliest.released).total_seconds()
    timespan_h = timespan_s / 60 / 60

    interval = int(timespan_h / count)
    logger.info('%d episodes in %d days => %dh interval', count,
        timespan_h / 24, interval)

    # place interval between {MIN,MAX}_UPDATE_INTERVAL
    interval = max(interval, MIN_UPDATE_INTERVAL)
    interval = min(interval, MAX_UPDATE_INTERVAL)

    return interval
