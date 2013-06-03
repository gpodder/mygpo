from base64 import b64decode
from optparse import make_option
import sys

from couchdb.multipart import write_multipart

from django.core.management.base import BaseCommand

from mygpo.core.models import Podcast
from mygpo.directory.toplist import PodcastToplist
from mygpo.users.models import User
from mygpo.utils import progress
from mygpo.core.json import json
from mygpo.db.couchdb import get_main_database
from mygpo.db.couchdb.episode import episodes_for_podcast
from mygpo.db.couchdb.podcast import podcast_by_id, podcast_for_url
from mygpo.db.couchdb.podcast_state import podcast_states_for_user, \
    all_podcast_states
from mygpo.db.couchdb.episode_state import episode_state_for_user_episode, \
    all_episode_states
from mygpo.db.couchdb.user import suggestions_for_user
from mygpo.db.couchdb.directory import category_for_tag

import logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Dumps a Sample of the whole Database that can be used for
    testing/development. All objects that are (indirectly) referenced
    be the users specified by --user args are dumped.

    The dump is similar to a dump of couchdb-python's couchdb-dump and
    can be imported by its couchdb-load
    """


    option_list = BaseCommand.option_list + (
        make_option('--user', action='append', type="string", dest='users', default=[],
            help="User for which related data should be dumped"),
        make_option('--toplist', action='store_true', dest='toplist',
            help="Dump toplist podcasts"),
        make_option('--podcast', action='append', type="string", dest='podcasts', default=[],
            help="Feed-URLs of podcasts to dump"),
    )


    def handle(self, *args, **options):

        docs = set()
        progress(0, len(docs), '', stream=sys.stderr)

        for username in options.get('users', []):
            user = User.get_user(username)
            self.add_user_recursive(user, docs)

        if options.get('toplist', False):
            toplist = PodcastToplist()
            for n, podcast in toplist[:25]:
                self.add_podcast_recursive(podcast, docs)

        for podcast_url in options.get('podcasts'):
            podcast = podcast_for_url(podcast_url, docs)
            if not podcast:
                logger.warn('podcast not found for URL "%s"', podcast_url)

            else:
                self.add_podcast_recursive(podcast, docs)

        db = get_main_database()
        docs = sorted(docs)
        self.dump(docs, db)


    def add_user_recursive(self, user, docs):
        """ adds a user and all the podcast and episodes it references """

        # User
        docs.add(user._id)

        # Suggestions
        suggestions = suggestions_for_user(user)
        docs.add(suggestions._id)

        progress(0, len(docs), '', stream=sys.stderr)

        # Podcast States
        for p_state in podcast_states_for_user(user):
            self.add_podcast_state(p_state, docs)

            progress(0, len(docs), p_state, stream=sys.stderr)

            # Podcast
            podcast = podcast_by_id(p_state.podcast)
            self.add_podcast(podcast, docs)

            progress(0, len(docs), podcast, stream=sys.stderr)

            # Episodes
            for episode in episodes_for_podcast(podcast):
                self.add_episode(episode, docs)
                progress(0, len(docs), episode, stream=sys.stderr)

                e_state = episode_state_for_user_episode(user, episode)
                self.add_episode_state(e_state, docs)
                progress(0, len(docs), e_state, stream=sys.stderr)


    def add_podcast_recursive(self, podcast, docs):
        self.add_podcast(podcast, docs)

        progress(0, len(docs), podcast, stream=sys.stderr)

        states = all_podcast_states(podcast)
        for state in states:
            self.add_podcast_state(state, docs)
            progress(0, len(docs), state, stream=sys.stderr)

        # Episodes
        for episode in episodes_for_podcast(podcast.get_podcast()):
            self.add_episode(episode, docs)
            progress(0, len(docs), episode, stream=sys.stderr)

            states = all_episode_states(episode)
            for state in states:
                self.add_episode_state(state, docs)
                progress(0, len(docs), state, stream=sys.stderr)


    def add_podcast_state(self, p_state, docs):
        docs.add(p_state._id)

        # Categories
        for tag in p_state.tags:
            c = category_for_tag(tag)
            if c:
                docs.add(c._id)


    def add_podcast(self, podcast, docs):
        docs.add(podcast._id)

        # if podcast is actually a PodcastGroup, we get the first podcast
        podcast=podcast.get_podcast()

        # Categories
        for s in podcast.tags:
            for tag in podcast.tags[s]:
                c = category_for_tag(tag)
                if c:
                    docs.add(c._id)


    def add_episode(self, episode, docs):
        docs.add(episode._id)


    def add_episode_state(self, e_state, docs):
        if e_state._id:
            docs.add(e_state._id)



    def dump(self, docs, db):

        output = sys.stdout
        boundary = None
        envelope = write_multipart(output, boundary=boundary)
        total = len(docs)

        for n, docid in enumerate(docs):

            if not docid:
                continue

            doc = db.get(docid, attachments=True)
            attachments = doc.pop('_attachments', {})
            jsondoc = json.dumps(doc)

            if attachments:
                parts = envelope.open({
                    'Content-ID': doc['_id'],
                    'ETag': '"%s"' % doc['_rev']
                })
                parts.add('application/json', jsondoc)

                for name, info in attachments.items():
                    content_type = info.get('content_type')
                    if content_type is None:  # CouchDB < 0.8
                        content_type = info.get('content-type')
                    parts.add(content_type, b64decode(info['data']), {
                        'Content-ID': name
                    })
                parts.close()

            else:
                envelope.add('application/json', jsondoc, {
                    'Content-ID': doc['_id'],
                    'ETag': '"%s"' % doc['_rev']
                })

            progress(n+1, total, docid, stream=sys.stderr)

        envelope.close()
