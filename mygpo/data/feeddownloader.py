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

import sys
import os.path
import urllib2
import hashlib
from datetime import datetime
from itertools import chain

from mygpo.core.models import Episode, Podcast, PodcastGroup
from mygpo.core.slugs import assign_missing_episode_slugs, assign_slug, \
         PodcastSlug
from feedservice.parse import parse_feed
from feedservice.parse.text import convert_markdown
from mygpo.utils import file_hash
from mygpo.web.logo import CoverArt





class PodcastUpdater(object):
    """ Updates a number of podcasts with data from their feeds """

    def __init__(self, queue):
        """ Queue is an iterable of podcast objects """
        self.queue = queue


    def update(self):
        """ Run the updates """

        for n, podcast in enumerate(self.queue):

            if isinstance(podcast, PodcastGroup):
                for p in podcast.podcasts:
                    print '(%d) %s' % (n, p.url)
                    self.update_podcast(podcast)

            else:
                print '(%d) %s' % (n, podcast.url)
                self.update_podcast(podcast)


    def update_podcast(self, podcast):
        parsed = parse_feed(podcast.url, process_text=convert_markdown)

        if 'urls' not in parsed:
            # TODO ?
            return

        podcast = Podcast.for_url(parsed['urls'][0])

        # TODO: check if we changed something
        updated = True

        podcast.title = parsed.get('title', podcast.title)
        podcast.urls = list(set(podcast.urls + parsed['urls']))
        podcast.description = parsed.get('description', podcast.description)
        podcast.link = parsed.get('link', podcast.link)
        podcast.last_update = datetime.utcnow()
        podcast.logo_url = parsed.get('logo', podcast.logo_url)
        podcast.author = parsed.get('author', podcast.author)
        podcast.language = parsed.get('language', podcast.language)
        podcast.content_types = parsed.get('content_types', podcast.content_types)
        podcast.tags['feed'] = parsed.get('tags', podcast.tags['feed'])
        podcast.common_episode_title = parsed.get('common_episode_title', podcast.common_episode_title)
        podcast.new_location = parsed.get('new_location', podcast.new_location)


        if podcast.new_location:
            self.mark_outdated(podcast)

        episodes = list(podcast.get_episodes())
        self.update_episodes(podcast, parsed, episodes)

        # latest episode timestamp
        eps = filter(lambda e: bool(e.released), episodes)
        eps = sorted(eps, key=lambda e: e.released)
        if eps:
            podcast.latest_episode_timestamp = eps[-1].released


        assign_slug(podcast, PodcastSlug)
        assign_missing_episode_slugs(podcast)

        self.save_podcast_logo(podcast.logo_url)


    def update_episodes(self, podcast, parsed, episodes):

        existing_episodes = dict( (e.url, e) for e in episodes)
        episodes_by_id = dict( (e._id, e) for e in existing_episodes.values())

        for parsed_episode in parsed['episodes']:


            parsed_url = None

            for f in parsed_episode['files']:
                if f['urls']:
                    parsed_url = f['urls'][0]

            if not parsed_url:
                continue

            episode = existing_episodes.pop(parsed_url, None)

            if not episode:
                episode = Episode.for_podcast_id_url(podcast.get_id(),
                    parsed_url, create=True)

            if not episode:
                episode = Episode()
                episode.podcast = podcast.get_id()


            episode.title = parsed_episode.get('title', episode.title)
            episode.description = parsed_episode.get('description', episode.description)
            episode.link = parsed_episode.get('link', episode.link)
            episode.released = datetime.utcfromtimestamp(parsed_episode['released'])
            episode.author = parsed_episode.get('author', episode.author)
            episode.duration = parsed_episode.get('duration', episode.duration)
            episode.filesize = parsed_episode['files'][0]['filesize']
            episode.language = parsed_episode.get('language', episode.language)
            episode.last_update = datetime.utcnow()
            episode.mimetypes = list(set(filter(None, [f.get('mimetype') for f in parsed_episode['files']])))

            urls = list(chain.from_iterable(f['urls'] for f in parsed_episode['files']))
            episode.urls = list(set(episode.urls + urls))

            #episode.content_types = None #TODO

            print 'Updating Episode: %s' % episode.title
            episode.save()

            episodes_by_id.pop(episode._id, None)


        outdated_episodes = episodes_by_id.values()

        # set episodes to be outdated, where necessary
        for e in filter(lambda e: not e.outdated, outdated_episodes):
            e.outdated = True
            e.save()


    def save_podcast_logo(self, cover_art):
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

        except Exception:
            raise
