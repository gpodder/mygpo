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

from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
from mygpo.api.models import Device, Podcast, Subscription, SubscriptionAction, UserProfile, EpisodeAction
from put_test import put_data
from django.http import HttpRequest
from mygpo.api.simple import subscriptions
from mygpo.api.advanced import devices
import time

try:
    #try to import the JSON module (if we are on Python 2.6)
    import json
except ImportError:
    # No JSON module available - fallback to simplejson (Python < 2.6)
    print "No JSON module available - fallback to simplejson (Python < 2.6)"
    import simplejson as json


class SyncTest(TestCase):
    # FIXME: Broken testcase - please fix!
    def tXest_sync_actions(self):
        # this test does not yet complete when run as a unit test
        # because django does not set up the views
        u  = User.objects.create(username='u')
        d1 = Device.objects.create(name='d1', type='other', user=u)
        d2 = Device.objects.create(name='d2', type='other', user=u)
        p1 = Podcast.objects.create(title='p1', url='http://p1.com/')
        p2 = Podcast.objects.create(title='p2', url='http://p2.com/')
        p3 = Podcast.objects.create(title='p3', url='http://p3.com/')
        p4 = Podcast.objects.create(title='p4', url='http://p4.com/')

        s1 = SubscriptionAction.objects.create(device=d1, podcast=p1, action='1')
        time.sleep(1)
        s2 = SubscriptionAction.objects.create(device=d2, podcast=p2, action='1')
        time.sleep(1)
        u2 = SubscriptionAction.objects.create(device=d2, podcast=p2, action='-1')
        time.sleep(1)
        s3 = SubscriptionAction.objects.create(device=d1, podcast=p3, action='1')
        time.sleep(1)
        s3_= SubscriptionAction.objects.create(device=d2, podcast=p3, action='1')
        time.sleep(1)
        s4 = SubscriptionAction.objects.create(device=d2, podcast=p4, action='1')
        time.sleep(1)
        u3 = SubscriptionAction.objects.create(device=d2, podcast=p3, action='-1')

        #d1: p1, p3
        #d2: p2, -p2, p3, p4, -p3

        d1.sync_with(d2)

        #d1: -p3, +p4
        #d2: +p1

        sa1 = d1.get_sync_actions()
        sa2 = d2.get_sync_actions()

        self.assertEqual( len(sa1), 2)
        self.assertEqual( len(sa2), 1)

        self.assertEqual( sa1[p4].device, d2)
        self.assertEqual( sa1[p4].podcast, p4)
        self.assertEqual( sa1[p4].action, 1)

        self.assertEqual( sa1[p3].device, d2)
        self.assertEqual( sa1[p3].podcast, p3)
        self.assertEqual( sa1[p3].action, -1)

        self.assertEqual( sa2[p1].device, d1)
        self.assertEqual( sa2[p1].podcast, p1)
        self.assertEqual( sa2[p1].action, 1)

class AdvancedAPITest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='adv', email='adv@mygpo')
        self.user.set_password('adv1')
        self.user.save()
        self.device1 = Device.objects.create(user=self.user, name='d1', uid='uid1', type='desktop')
        self.device2 = Device.objects.create(user=self.user, name='d2', uid='uid2', type='mobile')
        self.url1 = 'http://example.com/feed.rss'
        self.url2 = 'http://example.org/podcast.php'
        self.url3 = 'http://example.net/foo.xml'

        self.client = Client()
        l = self.client.login(username='adv', password='adv1')
        self.assertEqual(l, True)

    def test_device_list(self):
        response = self.client.get('/api/1/devices/%s.json' % self.user.username)
        json_list = response.content
        list = json.loads(json_list)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(list), 2)
        self.assertEqual(list[0], {u'id': u'uid1', u'caption': u'd1', u'type': u'desktop', u'subscriptions': 0})
        self.assertEqual(list[1], {u'id': u'uid2', u'caption': u'd2', u'type': u'mobile',  u'subscriptions': 0})

    def test_rename_device(self):
        req = {'caption': 'd2!', 'type': 'server'}
        reqs = json.dumps(req)

        self.client.post('/api/1/devices/%s/%s.json' % (self.user.username, self.device2.uid), data={'data': reqs})

        response = self.client.get('/api/1/devices/%s.json' % self.user.username)
        json_list = response.content
        list = json.loads(json_list)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(list), 2)
        self.assertEqual(list[0], {u'id': u'uid1', u'caption': u'd1',  u'type': u'desktop', u'subscriptions': 0})
        self.assertEqual(list[1], {u'id': u'uid2', u'caption': u'd2!', u'type': u'server',  u'subscriptions': 0})


    def test_add_remove_subscriptions(self):
        req = {"add": [self.url1, self.url2, self.url3]}
        reqs = json.dumps(req)

        #adding 3 subscriptions
        response = self.client.post('/api/1/subscriptions/%s/%s.json' % (self.user.username, self.device1.uid), data={'data': reqs})
        self.assertEqual(response.status_code, 200)

        resp = json.loads(response.content)
        add_timestamp = resp['timestamp']

        #qerying subscription changes
        response = self.client.get('/api/1/subscriptions/%s/%s.json' % (self.user.username, self.device1.uid), {'since': add_timestamp-1})
        changes = json.loads(response.content)

        self.assertEqual(changes['add'], [self.url1, self.url2, self.url3])
        self.assertEqual(len(changes['remove']), 0)

        #removing the 1st and 3rd subscription
        req = {"add": [], 'remove': [self.url1, self.url3]}
        reqs = json.dumps(req)
        time.sleep(1)
        response = self.client.post('/api/1/subscriptions/%s/%s.json' % (self.user.username, self.device1.uid), data={'data': reqs})
        self.assertEqual(response.status_code, 200)

        resp = json.loads(response.content)
        timestamp = resp['timestamp']

        #changes since beginning, should return 1 addition, 2 removals
        response = self.client.get('/api/1/subscriptions/%s/%s.json' % (self.user.username, self.device1.uid), {'since': add_timestamp-1})
        changes = json.loads(response.content)
        self.assertEqual(changes['add'], [self.url2])
        self.assertEqual(changes['remove'], [self.url1, self.url3])


    def test_episode_update(self):
        req =  [{"podcast": self.url1,
                 "episode": "http://example.com/files/s01e20.mp3",
                 "device": self.device1.uid,
                 "action": "download",
                 "timestamp": "2009-12-12T09:00:00"},
                {"podcast": self.url2,
                 "episode": "http://ftp.example.org/foo.ogg",
                 "action": "play",
                 "position": "01:00:00"}]
        reqs = json.dumps(req)
        response = self.client.post('/api/1/episodes/%s.json' % self.user.username, data={'data': reqs})
        self.assertEqual(response.status_code, 200)

        resp = json.loads(response.content)
        timestamp = resp['timestamp']

        response = self.client.get('/api/1/episodes/%s.json' % self.user.username)
        changes = json.loads(response.content)
        self.assertEqual(len(changes['actions']), 2)
        self.assertTrue(self.hash_subset({u'action': u'download', u'podcast': self.url1, u'episode': u'http://example.com/files/s01e20.mp3'}, changes['actions'][0]))
        self.assertTrue(self.hash_subset({u'action': u'play', u'podcast': self.url2, u'episode': u'http://ftp.example.org/foo.ogg'}, changes['actions'][1]))

#        #currently fails, seems to be a bug in the test client
#        response = self.client.get('/api/1/episodes/%s.json' % self.user.username, {'podcast': self.url2})
#        self.assertEqual(response.status_code, 200)
#        changes = json.loads(response.content)
#        self.assertEqual(len(changes['actions']), 1)
#        self.assertTrue(self.hash_subset({u'action': u'play', u'podcast': self.url2, u'episode': u'http://ftp.example.org/foo.ogg'}, changes['actions'][0]))


    def hash_subset(self, hash1, hash2):
        for x in hash1.keys():
            if not x in hash2:
                return False
            if hash2[x] != hash1[x]:
                return False
        return True


class SimpleAPITest(TestCase):

    def setUp(self):
        un = 'u'
        pw = 'u'
        u  = User.objects.create(username=un, password=pw)
        UserProfile.objects.create(user=u)
        
        r = HttpRequest()
        r.method = 'PUT'
        r.user = u
        
        self.user = u
        self.req = r

    def test_put_get_txt(self):
        p1 = 'http://www.podcast1.com'
        p2 = 'http://www.podcast2.com'
        p3 = 'http://www.podcast3.com'
    
        d1 = '1'
        f1 = 'txt'
    
        data_txt_1 = '%s\n%s\n' % (p1, p2)
        data_txt_2 = '%s\n%s\n' % (p2, p3)
        
        #1. put 2 new podcasts
        self.req.raw_post_data = data_txt_1
        put = subscriptions(request=self.req, username=self.user.username, device_uid=d1, format=f1)
        # Successful requests should return the empty string + status code 200
        self.assertEqual(put.status_code, 200)
        self.assertEqual(put.content, '')
        
        #device 1 txt
        device = Device.objects.get(uid=d1, user=self.user)
        
        #get subscriptions
        s = [p.podcast for p in device.get_subscriptions()]
        urls = [p.url for p in s]
        self.assertEqual(len(urls), 2)
        self.assertEqual(urls[0], p1)
        self.assertEqual(urls[1], p2) 
        
        #2. put 1 new podcast and delete 1 old
        time.sleep(1)
        self.req.raw_post_data = data_txt_2
        subscriptions(request=self.req, username=self.user.username, device_uid=d1, format=f1)
        
        #get subscriptions
        s = [p.podcast for p in device.get_subscriptions()]
        urls = [p.url for p in s]
        self.assertEqual( len(s), 2)
        self.assertEqual(urls[0], p2)
        self.assertEqual(urls[1], p3) 
        
    def test_put_get_json(self):
    
        p1 = 'http://www.podcast1.com'
        p2 = 'http://www.podcast2.com'
        p3 = 'http://www.podcast3.com'

        d2 = '2'
        f2 = 'json'
    
        data_json_1 = '[\n"%s",\n"%s"\n]' % (p1, p2)
        data_json_2 = '[\n"%s",\n"%s"\n]' % (p2, p3)
    
        #1. put 2 new podcasts
        self.req.raw_post_data = data_json_1
        subscriptions(request=self.req, username=self.user.username, device_uid=d2, format=f2)
        
        #device 2 json
        device = Device.objects.get(uid=d2, user=self.user)
        
        #get subscriptions
        s = [p.podcast for p in device.get_subscriptions()]
        urls = [p.url for p in s]
        self.assertEqual( len(s), 2)
        self.assertEqual(urls[0], p1)
        self.assertEqual(urls[1], p2) 

        #2. put 1 new podcast and delete 1 old
        time.sleep(1)
        self.req.raw_post_data = data_json_2
        subscriptions(request=self.req, username=self.user.username, device_uid=d2, format=f2)
        
        #get subscriptions
        s = [p.podcast for p in device.get_subscriptions()]
        urls = [p.url for p in s]
        self.assertEqual( len(s), 2)
        self.assertEqual(urls[0], p2)
        self.assertEqual(urls[1], p3) 
        
    def test_put_get_opml(self):
        
        p1 = 'http://www.podcast1.com'
        p2 = 'http://www.podcast2.com'
        p3 = 'http://www.podcast3.com'
    
        d3 = '3'
        f3 = 'opml'  
        
        data_opml_1 = '<?xml version="1.0" encoding="UTF-8"?>\n<opml version="2.0">\n<head>\n<title>subscription list</title>\n\
                       <dateCreated>Tue, 01 Dec 2009 10:06:18 +0000</dateCreated>\n</head>\n<body>\n\
                       <outline text="p1" title="p1" type="rss" xmlUrl="%s"/>\n\
                       <outline text="p2" title="p2" type="rss" xmlUrl="%s"/>\n\
                       </body>\n</opml>\n' % (p1, p2)
        data_opml_2 = '<?xml version="1.0" encoding="UTF-8"?><opml version="2.0"><head><title>subscription list</title>\
                       <dateCreated>Tue, 01 Dec 2009 10:06:18 +0000</dateCreated></head><body>\
                       <outline text="p2" title="p2" type="rss" xmlUrl="%s"/>\
                       <outline text="p3" title="p3" type="rss" xmlUrl="%s"/>\
                       </body></opml>' % (p2, p3)
      
        #1. put 2 new podcasts
        self.req.raw_post_data = data_opml_1
        subscriptions(request=self.req, username=self.user.username, device_uid=d3, format=f3)
      
        #device 3 opml
        device = Device.objects.get(uid=d3, user=self.user)
        
        #get subscriptions
        s = [p.podcast for p in device.get_subscriptions()]
        urls = [p.url for p in s]
        self.assertEqual( len(s), 2)
        self.assertEqual(urls[0], p1)
        self.assertEqual(urls[1], p2) 
        
        #2. put 1 new podcast and delete 1 old
        time.sleep(1)
        self.req.raw_post_data = data_opml_2
        subscriptions(request=self.req, username=self.user.username, device_uid=d3, format=f3)
        
        #get subscriptions
        s = [p.podcast for p in device.get_subscriptions()]
        urls = [p.url for p in s]
        self.assertEqual( len(s), 2)
        self.assertEqual(urls[0], p2)
        self.assertEqual(urls[1], p3) 

