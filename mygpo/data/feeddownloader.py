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

from mygpo.data import feedcore
from mygpo.api import models
from mygpo.data.models import PodcastTag
from mygpo.utils import parse_time
from mygpo.api.sanitizing import sanitize_url, rewrite_podcasts
from mygpo.data import youtube
from mygpo.data.mimetype import get_mimetype, check_mimetype, get_podcast_types

socket.setdefaulttimeout(10)
fetcher = feedcore.Fetcher(USER_AGENT)


def mark_outdated(podcast):
    for e in models.Episode.objects.filter(podcast=podcast):
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

    return set(tags)


def update_feed_tags(podcast, tags):
    src = 'feed'

    #delete all tags not found in the feed anymore
    PodcastTag.objects.filter(podcast=podcast, source=src).exclude(tag__in=tags).delete()

    #create new found tags
    for tag in tags:
        if not PodcastTag.objects.filter(podcast=podcast, source=src, tag=tag).exists():
            PodcastTag.objects.get_or_create(podcast=podcast, source=src, tag=tag)


def get_episode_metadata(entry, url, mimetype):
    d = {
            'url': url,
            'title': entry.get('title', entry.get('link', '')),
            'description': get_episode_summary(entry),
            'link': entry.get('link', ''),
            'timestamp': None,
            'author': entry.get('author', entry.get('itunes_author', '')),
            'duration': get_duration(entry),
            'filesize': get_filesize(entry, url),
            'language': entry.get('language', ''),
            'outdated': False,
            'mimetype': mimetype,
    }
    try:
        d['timestamp'] = datetime.datetime(*(entry.updated_parsed)[:6])
    except:
        d['timestamp'] = None

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

            if cover_art is not None:
                try:
                    image_sha1 = hashlib.sha1()
                    image_sha1.update(cover_art)
                    image_sha1 = image_sha1.hexdigest()
                    filename = os.path.join('..', 'htdocs', 'media', 'logo', image_sha1)
                    fp = open(filename, 'w')
                    fp.write(urllib2.urlopen(cover_art).read())
                    fp.close()
                    print >>sys.stderr, 'LOGO @', cover_art
                    podcast.logo_url = cover_art
                except Exception, e:
                    podcast.logo_url = None
                    print >>sys.stderr, 'cannot save image: %s' % e

            update_feed_tags(podcast, get_feed_tags(feed.feed))

            existing_episodes = list(models.Episode.objects.filter(podcast=podcast))

            for entry in feed.entries:
                try:
                    url, mimetype = get_episode_url(entry)
                    if url is None:
                        print 'Ignoring entry'
                        continue

                    url = sanitize_url(url, podcast=False, episode=True)
                    md = get_episode_metadata(entry, url, mimetype)
                    e, created = models.Episode.objects.get_or_create(
                        podcast=podcast,
                        url=url,
                        defaults=md)
                    if created:
                        print 'New episode: ', e.title.encode('utf-8', 'ignore')
                    else:
                        print 'Updating', e.title.encode('utf-8', 'ignore')
                        for key in md:
                            setattr(e, key, md[key])

                    # we need to distinguish it from non-updated episodes
                    if not e.title:
                        e.outdated = True
                    else:
                        e.outdated = False
                    e.save()

                    if e in existing_episodes:
                        existing_episodes.remove(e)

                except Exception, e:
                    print 'Cannot get episode:', e

            # all episodes that could not be found in the feed
            for e in existing_episodes:
                if not e.outdated:
                    e.outdated = True
                    e.save()

            podcast.content_types = get_podcast_types(podcast)

        except Exception, e:
            print >>sys.stderr, 'Exception:', e

        podcast.last_update = datetime.datetime.now()
        try:
            podcast.save()
        except Exception, e:
            print e


