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

USER_AGENT = 'mygpo crawler (+http://my.gpodder.org)'


import os
import sys
from datetime import datetime, timedelta
import hashlib
import urllib2
import socket
from glob import glob
from functools import partial
from itertools import chain

from mygpo.decorators import repeat_on_conflict
from mygpo.data import feedcore
from mygpo.utils import parse_time, file_hash
from mygpo.api.sanitizing import sanitize_url, rewrite_podcasts
from mygpo.data import youtube
from mygpo.data.mimetype import get_mimetype, check_mimetype, get_podcast_types
from mygpo.core.models import Episode, Podcast
from mygpo.core.slugs import assign_missing_episode_slugs, assign_slug, \
         PodcastSlug
from mygpo.web.logo import CoverArt

fetcher = feedcore.Fetcher(USER_AGENT)

def mark_outdated(podcast):
    for e in podcast.get_episodes():
        e.outdated = True
        e.save()

def get_episode_url(entry):
    """Get the download / episode URL of a feedparser entry"""
    enclosures = getattr(entry, 'enclosures', [])
    for enclosure in enclosures:
        if 'href' in enclosure:
            mimetype = get_mimetype(enclosure.get('type', ''), enclosure['href'])
            if check_mimetype(mimetype):
                return enclosure['href'], mimetype

    media_content = getattr(entry, 'media_content', [])
    for media in media_content:
        if 'url' in media:
            mimetype = get_mimetype(media.get('type', ''), media['url'])
            if check_mimetype(mimetype):
                return media['url'], mimetype

    links = getattr(entry, 'links', [])
    for link in links:
        if not hasattr(link, 'href'):
            continue

        if youtube.is_video_link(link['href']):
            return link['href'], 'application/x-youtube'

        # XXX: Implement link detection as in gPodder

    return None, None

def get_episode_summary(entry):
    for key in ('summary', 'subtitle', 'link'):
        value = entry.get(key, None)
        if value:
            return value

    return ''

def get_duration(entry):
    str = entry.get('itunes_duration', '')

    try:
        return parse_time(str)
    except (ValueError, TypeError):
        return 0

def get_filesize(entry, url):
    enclosures = getattr(entry, 'enclosures', [])
    for enclosure in enclosures:
        if 'href' in enclosure and enclosure['href'] == url:
            if 'length' in enclosure:
                try:
                    return int(enclosure['length'])
                except ValueError:
                    return None

            return None
    return None


def get_feed_tags(feed):
    tags = []

    for tag in feed.get('tags', []):
        if tag['term']:
            tags.extend([t for t in tag['term'].split(',') if t])

        if tag['label']:
            tags.append(tag['label'])

    return list(set(tags))


def get_episode_metadata(entry, url, mimetype, podcast_language):
    d = {
            'url': url,
            'title': entry.get('title', entry.get('link', '')),
            'description': get_episode_summary(entry),
            'link': entry.get('link', ''),
            'author': entry.get('author', entry.get('itunes_author', '')),
            'duration': get_duration(entry),
            'filesize': get_filesize(entry, url),
            'language': entry.get('language', podcast_language),
            'mimetypes': [mimetype],
    }
    try:
        d['released'] = datetime(*(entry.updated_parsed)[:6])
    except:
        d['released'] = None

    # set outdated true if we didn't find a title (so that the
    # feed-downloader doesn't try again infinitely
    d['outdated'] = not d['title']

    return d


def get_podcast_metadata(podcast, feed):

    episodes = list(podcast.get_episodes())

    return dict(
        title = feed.feed.get('title', podcast.url),
        link = feed.feed.get('link', podcast.url),
        description = feed.feed.get('subtitle', podcast.description),
        author = feed.feed.get('author', feed.feed.get('itunes_author', podcast.author)),
        language = feed.feed.get('language', podcast.language),
        logo_url = get_podcast_logo(podcast, feed),
        content_types = get_podcast_types(episodes),
        latest_episode_timestamp = get_latest_episode_timestamp(episodes),
        episode_count = podcast.get_episode_count()
    )


def get_latest_episode_timestamp(episodes):

    timestamps = filter(None, [e.released for e in episodes])

    if not timestamps:
        return None

    max_timestamp = max(timestamps)


    max_future = datetime.utcnow() + timedelta(days=2)

    if max_timestamp > max_future:
        return datetime.utcnow()

    return max_timestamp



def update_podcasts(fetch_queue):
    for n, podcast in enumerate(fetch_queue):
        print '(%d) %s' % (n, podcast.url)

        try:
            timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(60)
            fetcher.fetch(podcast.url)
            socket.setdefaulttimeout(timeout)

        except (feedcore.Offline, feedcore.InvalidFeed, feedcore.WifiLogin,
                feedcore.AuthenticationRequired, socket.error, IOError):
            print 'marking outdated'
            mark_outdated(podcast)

        except feedcore.NewLocation, location:
            print 'redirecting to', location.data
            new_url = sanitize_url(location.data)
            if new_url:

                p = Podcast.for_url(new_url)
                if not p:
                    podcast.urls.insert(0, new_url)
                    fetch_queue = chain([podcast], fetch_queue)
                else:
                    print 'podcast with new URL found, outdating old one'
                    podcast.new_location = new_url
                    podcast.save()
                    mark_outdated(podcast)

        except feedcore.UpdatedFeed, updated:
            feed = updated.data

            existing_episodes = list(podcast.get_episodes())
            update_ep = partial(update_episode, podcast=podcast)
            feed_episodes = filter(None, map(update_ep, feed.entries))
            outdated_episodes = set(existing_episodes) - set(feed_episodes)

            # set episodes to be outdated, where necessary
            for e in filter(lambda e: not e.outdated, outdated_episodes):
                e.outdated = True
                e.save()


            podcast_md = get_podcast_metadata(podcast, feed)

            changed = False
            for key, value in podcast_md.items():
                if getattr(podcast, key) != value:
                    setattr(podcast, key, value)
                    changed = True

            tags = get_feed_tags(feed.feed)
            if podcast.tags.get('feed', None) != tags:
                podcast.tags['feed'] = tags
                changed = True

            if changed:
                print 'updating podcast'
                podcast.last_update = datetime.utcnow()
                podcast.save()
            else:
                print 'podcast not updated'


        except Exception, e:
            print podcast.url
            print >>sys.stderr, 'Exception:', e


        assign_slug(podcast, PodcastSlug)
        assign_missing_episode_slugs(podcast)


def get_podcast_logo(podcast, feed):
    cover_art = podcast.logo_url
    image = feed.feed.get('image', None)
    if image is not None:
        for key in ('href', 'url'):
            cover_art = getattr(image, key, None)
            if cover_art:
                break

    if podcast.link:
        yturl = youtube.get_real_cover(podcast.link)
        if yturl:
            cover_art = yturl

    if cover_art:
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

        except Exception, e:
            if str(e).strip():
                try:
                    print >> sys.stderr, \
                        unicode('cannot save image for podcast %s: %s'
                        % (podcast.get_id(), str(e)), errors='ignore')
                except:
                    print >> sys.stderr, 'cannot save podcast logo'

            return None



def update_episode(entry, podcast):
    url, mimetype = get_episode_url(entry)

    if url is None:
        print 'Ignoring entry'
        return

    url = sanitize_url(url, 'episode')
    if not url:
        print 'Ignoring entry'
        return

    episode = Episode.for_podcast_id_url(podcast.get_id(),
            url, create=True)
    md = get_episode_metadata(entry, url, mimetype,
            podcast.language)

    changed = False
    for key, value in md.items():
        if getattr(episode, key) != value:
            setattr(episode, key, value)
            changed = True

    if changed:
        episode.save()
        print 'Updating Episode: %s' % episode.title.encode('utf-8', 'ignore')

    return episode
