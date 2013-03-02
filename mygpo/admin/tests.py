"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

import time
from datetime import datetime

from django.test import TestCase

from mygpo.users.models import User, Device, EpisodeAction
from mygpo.core.models import Podcast, Episode
from mygpo.counter import Counter
from mygpo.maintenance.merge import PodcastMerger
from mygpo.db.couchdb.episode import episode_by_id, episodes_for_podcast
from mygpo.db.couchdb.podcast import podcast_by_id
from mygpo.db.couchdb.podcast_state import podcast_state_for_user_podcast
from mygpo.db.couchdb.episode_state import episode_state_for_user_episode
from mygpo.utils import get_timestamp


class SimpleTest(TestCase):

    def test_merge(self):

        p1 = Podcast()
        p1.urls = ['http://example.com/podcast1.rss']
        p1.save()

        p2 = Podcast()
        p2.urls = ['http://example.com/podcast2.rss']
        p2.save()


        e1 = Episode()
        e1.title = 'Episode 1'
        e1.podcast = p1.get_id()
        e1.urls = ['http://example.com/podcast1/e1.mp3']
        e1.save()

        e2 = Episode()
        e2.title = 'Episode 2'
        e2.podcast = p1.get_id()
        e2.urls = ['http://example.com/podcast1/e2.mp3']
        e2.save()

        e3 = Episode()
        e3.title = 'Episode 3'
        e3.podcast = p2.get_id()
        e3.urls = ['http://example.com/podcast2/e2.mp3']
        e3.save()

        e4 = Episode()
        e4.title = 'Episode 4'
        e4.podcast = p2.get_id()
        e4.urls = ['http://example.com/podcast2/e3.mp3']
        e4.save()

        user = User()
        user.username = 'user-test_merge'
        user.email = 'user-test_merge@example.com'
        user.set_password('secret')

        device1 = Device()
        device1.uid = 'dev1'

        device2 = Device()
        device2.uid = 'dev2'

        user.devices.append(device1)
        user.devices.append(device2)
        user.save()


        p1.subscribe(user, device1)
        time.sleep(1)
        p1.unsubscribe(user, device1)
        time.sleep(1)
        p1.subscribe(user, device1)
        p2.subscribe(user, device2)

        s1 = episode_state_for_user_episode(user, e1)
        s1.add_actions([EpisodeAction(action='play',
                    upload_timestamp=get_timestamp(datetime.utcnow()))])
        s1.save()

        s3 = episode_state_for_user_episode(user, e3)
        s3.add_actions([EpisodeAction(action='play',
                    upload_timestamp=get_timestamp(datetime.utcnow()))])
        s3.save()

        # we need that for later
        e3_id = e3._id

        actions = Counter()

        # decide which episodes to merge
        groups = [(0, [e1]), (1, [e2, e3]), (2, [e4])]

        # carry out the merge
        pm = PodcastMerger([p1, p2], actions, groups)
        pm.merge()

        e1 = episode_by_id(e1._id)
        es1 = episode_state_for_user_episode(user, e1)
        self.assertEqual(len(es1.actions), 1)

        # check if merged episode's id can still be accessed
        e3 = episode_by_id(e3_id)
        es3 = episode_state_for_user_episode(user, e3)
        self.assertEqual(len(es3.actions), 1)

        p1 = podcast_by_id(p1.get_id())
        ps1 = podcast_state_for_user_podcast(user, p1)
        self.assertEqual(len(ps1.get_subscribed_device_ids()), 2)

        self.assertEqual(len(list(episodes_for_podcast(p1))), 3)
