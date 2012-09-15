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
from feedservice.parse.text import ConvertMarkdown
from mygpo.utils import file_hash, split_list
from mygpo.web.logo import CoverArt
from mygpo.couch import get_main_database





class PodcastUpdater(object):
    """ Updates a number of podcasts with data from their feeds """

    def __init__(self, queue):
        """ Queue is an iterable of podcast objects """
        self.queue = queue
        self.db = get_main_database()


    def update(self):
        """ Run the updates """

        for n, podcast in enumerate(self.queue):

            if isinstance(podcast, PodcastGroup):
                for m in range(len(podcast.podcasts)):
                    pg = PodcastGroup.get(podcast._id)
                    p = pg.podcasts[m]
                    print '{:5d} {:s}'.format(n, p.url)
                    self.update_podcast(p)

            else:
                print '{:5d} {:s}'.format(n, podcast.url)
                self.update_podcast(podcast)

            print


    def update_podcast(self, podcast):

        try:
            parsed = parse_feed(podcast.url, text_processor=ConvertMarkdown())

        except urllib2.HTTPError as e:
            if e.code in (404, 400):
                self.mark_outdated(podcast)
                return

            raise


        podcast = Podcast.for_url(parsed.urls[0])
        changed = False

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


        if podcast.new_location:
            new_podcast = Podcast.for_url(podcast.new_location)
            if podcast:
                self.mark_outdated(podcast)
                return

            else:
                podcast.urls.insert(0, podcast.new_location)
                changed = True


        episodes = self.update_episodes(podcast, parsed.episodes)

        # latest episode timestamp
        eps = filter(lambda e: bool(e.released), episodes)
        eps = sorted(eps, key=lambda e: e.released)
        if eps:
            changed |= update_a(podcast, 'latest_episode_timestamp', eps[-1].released)


        if changed:
            print '      saving podcast'
            podcast.last_update = datetime.utcnow()
            podcast.save()


        assign_slug(podcast, PodcastSlug)
        assign_missing_episode_slugs(podcast)

        self.save_podcast_logo(podcast.logo_url)


    def update_episodes(self, podcast, parsed_episodes):

        all_episodes = set(podcast.get_episodes())
        remaining = list(all_episodes)
        updated_episodes = []

        for parsed_episode in parsed_episodes:

            url = None

            for f in parsed_episode.files:
                if f.urls:
                    url = f.urls[0]

            if not url:
                continue

            # pop matchin episodes out of the "existing" list
            matching, remaining = split_list(remaining, lambda e: url in e.urls)

            if not matching:
                new_episode = Episode.for_podcast_id_url(podcast.get_id(),
                    url, create=True)
                matching = [new_episode]
                all_episodes.add(new_episode)


            for episode in matching:
                changed = False
                changed |= update_a(episode, 'title', parsed_episode.title or episode.title)
                changed |= update_a(episode, 'description', parsed_episode.description or episode.description)
                changed |= update_a(episode, 'content', parsed_episode.content or parsed_episode.description or episode.content)
                changed |= update_a(episode, 'link', parsed_episode.link or episode.link)
                changed |= update_a(episode, 'released', datetime.utcfromtimestamp(parsed_episode.released))
                changed |= update_a(episode, 'author', parsed_episode.author or episode.author)
                changed |= update_a(episode, 'duration', parsed_episode.duration or episode.duration)
                changed |= update_a(episode, 'filesize', parsed_episode.files[0].filesize)
                changed |= update_a(episode, 'language', parsed_episode.language or episode.language)
                changed |= update_a(episode, 'mimetypes', list(set(filter(None, [f.mimetype for f in parsed_episode.files]))))

                urls = list(chain.from_iterable(f.urls for f in parsed_episode.files))
                changed |= update_a(episode, 'urls', sorted(set(episode.urls + urls), key=len))

                if changed:
                    episode.last_update = datetime.utcnow()
                    updated_episodes.append(episode)

                #episode.content_types = None #TODO


        outdated_episodes = all_episodes - set(updated_episodes)

        # set episodes to be outdated, where necessary
        for e in filter(lambda e: not e.outdated, outdated_episodes):
            e.outdated = True
            updated_episodes.append(e)


        if updated_episodes:
            print '      Updating', len(updated_episodes), 'episodes'
            self.db.save_docs(updated_episodes)

        return all_episodes


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

            print '      LOGO @', cover_art

            # save new cover art
            with open(filename, 'w') as fp:
                fp.write(urllib2.urlopen(cover_art).read())

            # get hash of new file
            with open(filename) as f:
                new_hash = file_hash(f).digest()

            # remove thumbnails if cover changed
            if old_hash != new_hash:
                thumbnails = CoverArt.get_existing_thumbnails(prefix, filename)
                print '      Removing %d thumbnails' % len(thumbnails)
                for f in thumbnails:
                    os.unlink(f)

            return  cover_art

        except urllib2.HTTPError as e:
            print e

        except urllib2.URLError as e:
            print e


    def mark_outdated(self, podcast):
        print '      mark outdated'
        podcast.outdated = True
        podcast.last_update = datetime.utcnow()
        podcast.save()
        self.update_episodes(podcast, [])



_none = object()

def update_a(obj, attrib, value):
    changed = getattr(obj, attrib, _none) != value
    setattr(obj, attrib, value)
    return changed


def update_i(obj, item, value):
    changed = obj.get(item, _none) != value
    obj[item] = value
    return changed
