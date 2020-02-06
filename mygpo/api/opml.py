# -*- coding: utf-8 -*-

"""OPML importer and exporter (based on gPodder's "opml" module)

This module contains helper classes to import subscriptions from OPML files on
the web and to export a list of podcast objects to valid OPML 2.0 files.
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
        except ExpatError as e:
            raise ValueError from e

        for outline in doc.getElementsByTagName('outline'):
            if (
                outline.getAttribute('type') in self.VALID_TYPES
                and outline.getAttribute('xmlUrl')
                or outline.getAttribute('url')
            ):
                channel = {
                    'url': outline.getAttribute('xmlUrl')
                    or outline.getAttribute('url'),
                    'title': outline.getAttribute('title')
                    or outline.getAttribute('text')
                    or outline.getAttribute('xmlUrl')
                    or outline.getAttribute('url'),
                    'description': outline.getAttribute('text')
                    or outline.getAttribute('xmlUrl')
                    or outline.getAttribute('url'),
                }

                if channel['description'] == channel['title']:
                    channel['description'] = channel['url']

                for attr in ('url', 'title', 'description'):
                    channel[attr] = channel[attr].strip()

                self.items.append(channel)


class Exporter(object):
    """
    Helper class to export a list of channel objects to a local file in OPML
    2.0 format. See www.opml.org for the OPML specification.
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

            outline = doc.createElement('outline')

            if isinstance(channel, SubscribedPodcast):
                title = channel.podcast.title
                outline.setAttribute('xmlUrl', channel.ref_url)
                outline.setAttribute('description', channel.podcast.description or '')
                outline.setAttribute('type', 'rss')
                outline.setAttribute('htmlUrl', channel.podcast.link or '')
            elif isinstance(channel, PodcastGroup):
                title = channel.title
                for subchannel in channel.podcast_set.all():
                    outline.appendChild(create_outline(subchannel))
            else:
                title = channel.title
                outline.setAttribute('xmlUrl', channel.url)
                outline.setAttribute('description', channel.description or '')
                outline.setAttribute('type', 'rss')
                outline.setAttribute('htmlUrl', channel.podcast.link or '')

            outline.setAttribute('title', title or '')
            outline.setAttribute('text', title or '')
            return outline

        body = doc.createElement('body')
        for channel in channels:
            body.appendChild(create_outline(channel))
        opml.appendChild(body)

        return doc.toprettyxml(encoding='utf-8', indent='  ', newl=os.linesep)
