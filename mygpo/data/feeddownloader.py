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
import datetime
import hashlib
import urllib2
import socket

from mygpo.decorators import repeat_on_conflict
from mygpo import migrate
from mygpo.data import feedcore
from mygpo.api import models
from mygpo.utils import parse_time
from mygpo.api.sanitizing import sanitize_url, rewrite_podcasts
from mygpo.data import youtube
from mygpo.data.mimetype import get_mimetype, check_mimetype, get_podcast_types
from mygpo import migrate
from mygpo.core.models import Episode

socket.setdefaulttimeout(10)
fetcher = feedcore.Fetcher(USER_AGENT)


def mark_outdated(podcast):
    podcast = migrate.get_or_migrate_podcast(podcast)
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
    except ValueError:
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


@repeat_on_conflict()
def update_feed_tags(podcast, tags):
    src = 'feed'
    podcast.tags[src] = tags
    try:
        podcast.save()
    except Exception, e:
        from couchdbkit import ResourceConflict
        if isinstance(e, ResourceConflict):
            raise # and retry

        print >> sys.stderr, 'error saving tags for podcast %s: %s' % (np.get_id(), e)


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
        d['released'] = datetime.datetime(*(entry.updated_parsed)[:6])
    except:
        d['released'] = None

    # we need to distinguish it from non-updated episodes
    d['outdated'] = not d['title']

    return d


def update_podcasts(fetch_queue):
    n=0
    count = len(fetch_queue)

    for podcast in fetch_queue:
        n+=1
        print '(%d/%d) %s' % (n, count, podcast.url)

        try:
            fetcher.fetch(podcast.url)

        except (feedcore.Offline, feedcore.InvalidFeed, feedcore.WifiLogin, feedcore.AuthenticationRequired):
            mark_outdated(podcast)

        except feedcore.NewLocation, location:
            print location.data
            new_url = sanitize_url(location.data)
            if new_url:
                print new_url
                if not models.Podcast.objects.filter(url=new_url).exists():
                    podcast.url = new_url
                else:
                    p = models.Podcast.objects.get(url=new_url)
                    rewrite_podcasts(podcast, p)
                    podcast.delete()
                    continue

        except feedcore.UpdatedFeed, updated:
            feed = updated.data
            podcast.title = feed.feed.get('title', podcast.url)
            podcast.link = feed.feed.get('link', podcast.url)
            podcast.description = feed.feed.get('subtitle', podcast.description)
            podcast.author = feed.feed.get('author', feed.feed.get('itunes_author', podcast.author))
            podcast.language = feed.feed.get('language', podcast.language)

            cover_art = podcast.logo_url
            image = feed.feed.get('image', None)
            if image is not None:
                for key in ('href', 'url'):
                    cover_art = getattr(image, key, None)
                    if cover_art:
                        break

            yturl = youtube.get_real_cover(podcast.link)
            if yturl:
                cover_art = yturl

            if cover_art:
                try:
                    image_sha1 = hashlib.sha1()
                    image_sha1.update(cover_art)
                    image_sha1 = image_sha1.hexdigest()
                    filename = os.path.join(os.path.dirname(os.path.abspath(__file__ )), '..', '..', 'htdocs', 'media', 'logo', image_sha1)
                    fp = open(filename, 'w')
                    fp.write(urllib2.urlopen(cover_art).read())
                    fp.close()
                    print 'LOGO @', cover_art
                    podcast.logo_url = cover_art
                except Exception, e:
                    podcast.logo_url = None
                    if repr(e).strip():
                        print >> sys.stderr, 'cannot save image %s for podcast %d: %s' % (cover_art.encode('utf-8'), podcast.id, repr(e).encode('utf-8'))

            new_podcast = migrate.get_or_migrate_podcast(podcast)
            update_feed_tags(new_podcast, get_feed_tags(feed.feed))

            existing_episodes = list(new_podcast.get_episodes())

            for entry in feed.entries:
                try:
                    url, mimetype = get_episode_url(entry)
                    if url is None:
                        print 'Ignoring entry'
                        continue

                    url = sanitize_url(url, 'episode')

                    episode = Episode.for_podcast_id_url(new_podcast.get_id(),
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

                    if episode in existing_episodes:
                        existing_episodes.remove(episode)

                except Exception as e:
                    print 'Cannot get episode:', e
                    raise

            # all episodes that could not be found in the feed
            for e in existing_episodes:
                if not e.outdated:
                    e.outdated = True
                    e.save()

            podcast.content_types = get_podcast_types(new_podcast)

        except Exception, e:
            print >>sys.stderr, 'Exception:', e

        podcast.last_update = datetime.datetime.now()
        try:
            podcast.save()
        except Exception, e:
            print e


