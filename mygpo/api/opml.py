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

"""OPML importer and exporter (based on gPodder's "opml" module)

This module contains helper classes to import subscriptions from OPML files on
the web and to export a list of podcast objects to valid OPML 1.1 files.
"""

import os

import xml.dom.minidom
from xml.parsers.expat import ExpatError
import email.utils


class Importer(object):
    VALID_TYPES = ('rss', 'link')

    def __init__(self, content):
        """
        Parses the OPML feed from the given URL into a local data structure
        containing podcast metadata.
        """
        self.items = []

        try:
            doc = xml.dom.minidom.parseString(content)
        except ExpatError e:
            raise ValueError from e

        for outline in doc.getElementsByTagName('outline'):
            if outline.getAttribute('type') in self.VALID_TYPES and \
                    outline.getAttribute('xmlUrl') or \
                    outline.getAttribute('url'):
                channel = {
                    'url': outline.getAttribute('xmlUrl') or \
                           outline.getAttribute('url'),
                    'title': outline.getAttribute('title') or \
                             outline.getAttribute('text') or \
                             outline.getAttribute('xmlUrl') or \
                             outline.getAttribute('url'),
                    'description': outline.getAttribute('text') or \
                                   outline.getAttribute('xmlUrl') or \
                                   outline.getAttribute('url'),
                }

                if channel['description'] == channel['title']:
                    channel['description'] = channel['url']

                for attr in ('url', 'title', 'description'):
                    channel[attr] = channel[attr].strip()

                self.items.append(channel)


class Exporter(object):
    """
    Helper class to export a list of channel objects to a local file in OPML
    1.1 format. See www.opml.org for the OPML specification.
    """

    def __init__(self, title='my.gpodder.org Subscriptions'):
        self.title = title
        self.created = email.utils.formatdate(localtime=True)

    def generate(self, channels):
        """
        Creates a XML document containing metadata for each channel object in
        the "channels" parameter, which should be a list of channel objects.

        Returns: An OPML document as string
        """
        doc = xml.dom.minidom.Document()

        opml = doc.createElement('opml')
        opml.setAttribute('version', '2.0')
        doc.appendChild(opml)

        def create_node(name, content):
            node = doc.createElement(name)
            node.appendChild(doc.createTextNode(content))
            return node

        head = doc.createElement('head')
        head.appendChild(create_node('title', self.title or ''))
        head.appendChild(create_node('dateCreated', self.created))
        opml.appendChild(head)

        def create_outline(channel):
            from mygpo.subscriptions.models import SubscribedPodcast
            from mygpo.podcasts.models import PodcastGroup
            if isinstance(channel, SubscribedPodcast):
                title = channel.podcast.title
                description = channel.podcast.description
                url = channel.ref_url
            elif isinstance(channel, PodcastGroup):
                title = channel.title
                podcast = channel.podcast_set.first()
                description = podcast.description
                url = podcast.url
            else:
                title = channel.title
                description = channel.description
                url = channel.url

            outline = doc.createElement('outline')
            outline.setAttribute('title', title or '')
            outline.setAttribute('text', description or '')
            outline.setAttribute('xmlUrl', url)
            outline.setAttribute('type', 'rss')
            return outline

        body = doc.createElement('body')
        for channel in channels:
            body.appendChild(create_outline(channel))
        opml.appendChild(body)

        return doc.toprettyxml(encoding='utf-8', \
                               indent='  ', \
                               newl=os.linesep)
