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
from itertools import chain

from django.conf import settings

from mygpo.core.slugs import assign_missing_episode_slugs, assign_slug, \
         PodcastSlug
from feedservice.parse import parse_feed, FetchFeedException
from feedservice.parse.text import ConvertMarkdown
from feedservice.parse.models import ParserException
from mygpo.utils import file_hash, split_list
from mygpo.web.logo import CoverArt
from mygpo.db.couchdb.episode import episode_for_podcast_id_url, \
         episodes_for_podcast_uncached
from mygpo.db.couchdb.podcast import podcast_for_url
from mygpo.directory.tags import update_category
from mygpo.decorators import repeat_on_conflict
from mygpo.couch import get_main_database

import socket
socket.setdefaulttimeout(30)


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

        for n, podcast_url in enumerate(queue):
            print n, podcast_url
            try:
                self.update(podcast_url)

            except NoPodcastCreated as npc:
                print 'no podcast created:', npc
            print


    def update(self, podcast_url):
        """ Update the podcast for the supplied URL """

        try:
            parsed = self._fetch_feed(podcast_url)
            self._validate_parsed(parsed)

        except (ParserException, FetchFeedException) as ex:
            # if we fail to parse the URL, we don't even create the
            # podcast object
            p = podcast_for_url(podcast_url, create=False)
            if p:
                # if it exists already, we mark it as outdated
                self._mark_outdated(p)

            else:
                raise NoPodcastCreated(ex)

        assert parsed, 'fetch_feed must return something'
        p = podcast_for_url(podcast_url, create=True)
        self._update_podcast(p, parsed)
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

        if not parsed.episodes:
            raise NoEpisodesException('no episodes found')


    @repeat_on_conflict(['podcast'])
    def _update_podcast(self, podcast, parsed):
        """ updates a podcast according to new parser results """

        changed = False

        # we need that later to decide if we can "bump" a category
        prev_latest_episode_timestamp = podcast.latest_episode_timestamp

        changed |= update_a(podcast, 'title', parsed.title or podcast.title)
        changed |= update_a(podcast, 'urls', list(set(podcast.urls + parsed.urls)))
        changed |= update_a(podcast, 'description', parsed.description or podcast.description)
        changed |= update_a(podcast, 'link',  parsed.link or podcast.link)
        changed |= update_a(podcast, 'logo_url', parsed.logo or podcast.logo_url)
        changed |= update_a(podcast, 'author', parsed.author or podcast.author)
        changed |= update_a(podcast, 'language', parsed.language or podcast.language)
        changed |= update_a(podcast, 'content_types', parsed.content_types or podcast.content_types)
        changed |= update_i(podcast.tags, 'feed', parsed.tags or podcast.tags.get('feed', []))
        changed |= update_a(podcast, 'common_episode_title', parsed.common_title or podcast.common_episode_title)
        changed |= update_a(podcast, 'new_location', parsed.new_location or podcast.new_location)
        changed |= update_a(podcast, 'flattr_url', parsed.flattr)


        if podcast.new_location:
            new_podcast = podcast_for_url(podcast.new_location)
            if new_podcast != podcast:
                self._mark_outdated(podcast, 'redirected to different podcast')
                return

            elif not new_podcast:
                podcast.urls.insert(0, podcast.new_location)
                changed = True


        episodes = self._update_episodes(podcast, parsed.episodes)

        # latest episode timestamp
        eps = filter(lambda e: bool(e.released), episodes)
        eps = sorted(eps, key=lambda e: e.released)
        if eps:
            changed |= update_a(podcast, 'latest_episode_timestamp', eps[-1].released)
            changed |= update_a(podcast, 'episode_count', len(eps))


        self._update_categories(podcast, prev_latest_episode_timestamp)

        # try to download the logo and reset logo_url to None on http errors
        found = self._save_podcast_logo(podcast.logo_url)
        if not found:
            changed |= update_a(podcast, 'logo_url', None)

        if changed:
            print 'saving podcast'
            podcast.last_update = datetime.utcnow()
            podcast.save()


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


    @repeat_on_conflict(['podcast'])
    def _update_episodes(self, podcast, parsed_episodes):

        all_episodes = set(episodes_for_podcast_uncached(podcast))
        remaining = list(all_episodes)
        updated_episodes = []

        for parsed_episode in parsed_episodes:

            url = None

            for f in parsed_episode.files:
                if f.urls:
                    url = f.urls[0]

            if not url:
                continue

            guid = parsed_episode.guid

            # pop matchin episodes out of the "existing" list
            matching, remaining = split_list(remaining, lambda e: (e.guid and e.guid == guid) or url in e.urls)

            if not matching:
                new_episode = episode_for_podcast_id_url(podcast.get_id(),
                    url, create=True)
                matching = [new_episode]
                all_episodes.add(new_episode)


            for episode in matching:
                changed = False
                changed |= update_a(episode, 'guid', parsed_episode.guid or episode.guid)
                changed |= update_a(episode, 'title', parsed_episode.title or episode.title)
                changed |= update_a(episode, 'description', parsed_episode.description or episode.description)
                changed |= update_a(episode, 'content', parsed_episode.content or parsed_episode.description or episode.content)
                changed |= update_a(episode, 'link', parsed_episode.link or episode.link)
                changed |= update_a(episode, 'released', datetime.utcfromtimestamp(parsed_episode.released) if parsed_episode.released else episode.released)
                changed |= update_a(episode, 'author', parsed_episode.author or episode.author)
                changed |= update_a(episode, 'duration', parsed_episode.duration or episode.duration)
                changed |= update_a(episode, 'filesize', parsed_episode.files[0].filesize)
                changed |= update_a(episode, 'language', parsed_episode.language or episode.language)
                changed |= update_a(episode, 'mimetypes', list(set(filter(None, [f.mimetype for f in parsed_episode.files]))))
                changed |= update_a(episode, 'flattr_url', parsed_episode.flattr)

                urls = list(chain.from_iterable(f.urls for f in parsed_episode.files))
                changed |= update_a(episode, 'urls', sorted(set(episode.urls + urls), key=len))

                if changed:
                    episode.last_update = datetime.utcnow()
                    updated_episodes.append(episode)


        outdated_episodes = all_episodes - set(updated_episodes)

        # set episodes to be outdated, where necessary
        for e in filter(lambda e: not e.outdated, outdated_episodes):
            e.outdated = True
            updated_episodes.append(e)


        if updated_episodes:
            print 'Updating', len(updated_episodes), 'episodes'
            self.db.save_docs(updated_episodes)

        return all_episodes


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

            print 'LOGO @', cover_art

            # save new cover art
            with open(filename, 'w') as fp:
                fp.write(urllib2.urlopen(cover_art).read())

            # get hash of new file
            with open(filename) as f:
                new_hash = file_hash(f).digest()

            # remove thumbnails if cover changed
            if old_hash != new_hash:
                thumbnails = CoverArt.get_existing_thumbnails(prefix, filename)
                print 'Removing %d thumbnails' % len(thumbnails)
                for f in thumbnails:
                    os.unlink(f)

            return  cover_art

        except urllib2.HTTPError as e:
            print e

        except urllib2.URLError as e:
            print e


    @repeat_on_conflict(['podcast'])
    def _mark_outdated(self, podcast, msg=''):
        print 'mark outdated', msg
        podcast.outdated = True
        podcast.last_update = datetime.utcnow()
        podcast.save()
        self._update_episodes(podcast, [])



_none = object()

def update_a(obj, attrib, value):
    changed = getattr(obj, attrib, _none) != value
    setattr(obj, attrib, value)
    return changed


def update_i(obj, item, value):
    changed = obj.get(item, _none) != value
    obj[item] = value
    return changed
