"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

import time
from datetime import datetime
from collections import Counter

from django.test import TestCase

from mygpo.podcasts.models import Podcast, Episode
from mygpo.users.models import User, Device, EpisodeAction
from mygpo.maintenance.merge import PodcastMerger
from mygpo.db.couchdb.podcast_state import (podcast_state_for_user_podcast,
    subscribe, unsubscribe, )
from mygpo.db.couchdb.episode_state import episode_state_for_user_episode, \
    add_episode_actions
from mygpo.utils import get_timestamp


class SimpleTest(TestCase):

    def test_merge(self):

        p1 = Podcast.objects.get_or_create_for_url('http://example.com/podcast1.rss')
        p2 = Podcast.objects.get_or_create_for_url('http://example.com/podcast2.rss')

        e1 = Episode.objects.get_or_create_for_url(p1, 'http://example.com/podcast1/e1.mp3')
        e1.title = 'Episode 1'
        e1.save()

        e2 = Episode.objects.get_or_create_for_url(p2, 'http://example.com/podcast1/e2.mp3')
        e2.title = 'Episode 2'
        e2.save()

        e3 = Episode.objects.get_or_create_for_url(p2, 'http://example.com/podcast2/e2.mp3')
        e3.title = 'Episode 3'
        e3.save()

        e4 = Episode.objects.get_or_create_for_url(p2, 'http://example.com/podcast2/e3.mp3')
        e4.title = 'Episode 4'
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


        subscribe(p1, user, device1)
        time.sleep(1)
        unsubscribe(p1, user, device1)
        time.sleep(1)
        subscribe(p1, user, device1)
        subscribe(p2, user, device2)

        s1 = episode_state_for_user_episode(user, e1)
        add_episode_actions(s1, [EpisodeAction(action='play',
                    upload_timestamp=get_timestamp(datetime.utcnow()))])

        s3 = episode_state_for_user_episode(user, e3)
        add_episode_actions(s3, [EpisodeAction(action='play',
                    upload_timestamp=get_timestamp(datetime.utcnow()))])

        # we need that for later
        e3_id = e3.pk

        actions = Counter()

        # decide which episodes to merge
        groups = [(0, [e1]), (1, [e2, e3]), (2, [e4])]

        # carry out the merge
        pm = PodcastMerger([p1, p2], actions, groups)
        pm.merge()

        e1 = Episode.objects.get(pk=e1.pk)
        es1 = episode_state_for_user_episode(user, e1)
        self.assertEqual(len(es1.actions), 1)

        # check if merged episode's id can still be accessed
        e3 = Episode.objects.filter(podcast=p1).get_by_any_id(e3_id)
        es3 = episode_state_for_user_episode(user, e3)
        self.assertEqual(len(es3.actions), 1)

        p1 = Podcast.objects.get(pk=p1.get_id())
        ps1 = podcast_state_for_user_podcast(user, p1)
        self.assertEqual(len(ps1.get_subscribed_device_ids()), 2)

        episodes = p1.episode_set.all()
        self.assertEqual(len(episodes), 3)
