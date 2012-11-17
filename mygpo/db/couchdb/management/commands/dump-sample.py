from base64 import b64decode
from optparse import make_option
import sys

from couchdb.multipart import write_multipart

from django.core.management.base import BaseCommand
from mygpo.json import json

from mygpo.core.models import Podcast
from mygpo.couch import get_main_database
from mygpo.directory.toplist import PodcastToplist
from mygpo.users.models import PodcastUserState, EpisodeUserState, \
         Suggestions, User
from mygpo.utils import progress
from mygpo.json import json
from mygpo.db.couchdb.episode import episodes_for_podcast
from mygpo.db.couchdb.podcast import podcast_by_id
from mygpo.db.couchdb.podcast_state import podcast_states_for_user
from mygpo.db.couchdb.episode_state import episode_state_for_user_episode
from mygpo.db.couchdb.user import suggestions_for_user
from mygpo.db.couchdb.directory import category_for_tag


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
    )


    def handle(self, *args, **options):

        docs = set()

        for username in options.get('users', []):
            user = User.get_user(username)

            # User
            docs.add(user._id)

            # Suggestions
            suggestions = suggestions_for_user(user)
            docs.add(suggestions._id)

            # Podcast States
            for p_state in podcast_states_for_user(user):
                docs.add(p_state._id)

                # Categories
                for tag in p_state.tags:
                    c = category_for_tag(tag)
                    if c: docs.add(c._id)

                # Podcast
                podcast = podcast_by_id(p_state.podcast)
                docs.add(podcast._id)

                # Categories
                for s in podcast.tags:
                    for tag in podcast.tags[s]:
                        c = category_for_tag(tag)
                        if c: docs.add(c._id)

                # Episodes
                for episode in episodes_for_podcast(podcast):
                    docs.add(episode._id)

                    # Episode States
                    e_state = episode_state_for_user_episode(user, episode)
                    if e_state._id:
                        docs.add(e_state._id)

        if options.get('toplist', False):
            toplist = PodcastToplist()
            entries = toplist[:25]

            for n, podcast in entries:
                print n, podcast
                docs.add(podcast._id)

                # Episodes
                print podcast
                for episode in episodes_for_podcast(podcast):
                    docs.add(episode._id)


        db = get_main_database()
        docs = sorted(docs)
        self.dump(docs, db)


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
            jsondoc = json.encode(doc)

            if attachments:
                parts = envelope.open({
                    'Content-ID': doc['_id'],
                    'ETag': '"%s"' % doc['_rev']
                })
                parts.add('application/json', jsondoc)

                for name, info in attachments.items():
                    content_type = info.get('content_type')
                    if content_type is None: # CouchDB < 0.8
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
