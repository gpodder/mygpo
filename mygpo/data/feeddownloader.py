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
import time

from mygpo import feedcore
from mygpo.api import models
from mygpo.utils import parse_time

socket.setdefaulttimeout(10)
fetcher = feedcore.Fetcher(USER_AGENT)

def check_mime(mimetype):
    """Check if a mimetype is a "wanted" media type"""
    if '/' in mimetype:
        category, _ignore = mimetype.split('/', 1)
        return category in ('audio', 'video', 'image')
    else:
        return False

def get_episode_url(entry):
    """Get the download / episode URL of a feedparser entry"""
    enclosures = getattr(entry, 'enclosures', [])
    for enclosure in enclosures:
        if 'href' in enclosure and check_mime(enclosure.get('type', '')):
            return enclosure['href']

    media_content = getattr(entry, 'media_content', [])
    for media in media_content:
        if 'url' in media and check_mime(media.get('type', '')):
            return media['url']

    links = getattr(entry, 'links', [])
    for link in links:
        if not hasattr(link, 'href'):
            continue
        # XXX: Implement link detection as in gPodder

    return None

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
                return enclosure['length']

            return 0
    return 0

def get_episode_metadata(entry, url):
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
        except feedcore.Offline:
            pass
        except feedcore.InvalidFeed:
            pass
        except feedcore.WifiLogin:
            pass
        except feedcore.AuthenticationRequired:
            pass
        except feedcore.NewLocation, location:
            podcast.url = location.data
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
                image_sha1 = hashlib.sha1()
                image_sha1.update(cover_art)
                image_sha1 = image_sha1.hexdigest()
                filename = os.path.join('htdocs', 'media', 'logo', image_sha1)
                try:
                    fp = open(filename, 'w')
                    fp.write(urllib2.urlopen(cover_art).read())
                    fp.close()
                    print >>sys.stderr, 'LOGO @', cover_art
                    podcast.logo_url = cover_art
                except:
                    print >>sys.stderr, 'cannot save image'

            existing_episodes = list(models.Episode.objects.filter(podcast=podcast))

            for entry in feed.entries:
                try:
                    url = get_episode_url(entry)
                    if url is None:
                        print 'Ignoring entry'
                        continue
                    md = get_episode_metadata(entry, url)
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

        except Exception, e:
            print >>sys.stderr, 'Exception:', e

        podcast.last_update = datetime.datetime.now()
        try:
            podcast.save()
        except Exception, e:
            print e


