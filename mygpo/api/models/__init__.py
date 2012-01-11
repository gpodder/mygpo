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

from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
from django.utils.translation import ugettext as _
from mygpo.api.fields import SeparatedValuesField, JSONField
from mygpo import utils
import hashlib
import re

from mygpo.api.constants import EPISODE_ACTION_TYPES, DEVICE_TYPES, SUBSCRIBE_ACTION, SUBSCRIPTION_ACTION_TYPES
from mygpo.log import log

class UserProfile(models.Model):
    user = models.ForeignKey(User, unique=True, db_column='user_ptr_id')

    public_profile = models.BooleanField(default=True)
    generated_id = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)
    suggestion_up_to_date = models.BooleanField(default=False)
    settings = JSONField(default={})

    def __unicode__(self):
        return '%s (%s, %s)' % (self.user.username, self.public_profile, self.generated_id)

    class Meta:
        db_table = 'user'


class Podcast(models.Model):
    url = models.URLField(unique=True, verify_exists=False)
    title = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True, null=True)
    link = models.URLField(blank=True, null=True, verify_exists=False)
    last_update = models.DateTimeField(null=True,blank=True)
    logo_url = models.CharField(max_length=1000,null=True,blank=True)
    author = models.CharField(max_length=100, null=True, blank=True)
    language = models.CharField(max_length=10, null=True, blank=True)
    group = models.ForeignKey('PodcastGroup', null=True)
    group_member_name = models.CharField(max_length=20, default=None, null=True, blank=False)
    content_types = SeparatedValuesField(null=True, blank=True)

    def get_logo_url(self, size):
        if self.logo_url:
            sha = hashlib.sha1(self.logo_url).hexdigest()
            return '/logo/%d/%s.jpg' % (size, sha)
        else:
            return '/media/podcast-%d.png' % (hash(self.title) % 5, )


    def group_with(self, other, grouptitle, myname, othername):
        if self.group == other.group and self.group != None:
            return

        if self.group != None:
            if other.group == None:
                self.group.add(other, othername)

            else:
                raise ValueError('the podcasts are already in different groups')
        else:
            if other.group == None:
                g = PodcastGroup.objects.create(title=grouptitle)
                g.add(self, myname)
                g.add(other, othername)

            else:
                other.group.add(self, myname)

    def ungroup(self):
        if self.group == None:
            raise ValueError('the podcast currently isn\'t in any group')

        g = self.group
        self.group = None
        self.save()

        podcasts = Podcast.objects.filter(group=g)
        if podcasts.count() == 1:
            p = podcasts[0]
            p.group = None
            p.save()

    def __unicode__(self):
        return self.title if self.title != '' else self.url

    class Meta:
        db_table = 'podcast'


class PodcastGroup(models.Model):
    title = models.CharField(max_length=100, blank=False)

    @property
    def logo_url(self):
        return utils.first(p.logo_url for p in Podcast.objects.filter(group=self))

    def get_logo_url(self, size):
        return utils.first(p.get_logo_url(size) for p in Podcast.objects.filter(group=self))

    def add(self, podcast, membername):
        if podcast.group == self:
            podcast.group_member_name = membername

        elif podcast.group != None:
            podcast.ungroup()

        podcast.group = self
        podcast.group_member_name = membername
        podcast.save()

    def podcasts(self):
        return Podcast.objects.filter(group=self)

    def __unicode__(self):
        return self.title

    class Meta:
        db_table = 'podcast_groups'


# deprecated, only used in migration code
class Episode(models.Model):
    podcast = models.ForeignKey(Podcast)
    url = models.URLField(verify_exists=False)
    title = models.CharField(max_length=100, blank=True)
    description = models.TextField(null=True, blank=True)
    link = models.URLField(null=True, blank=True, verify_exists=False)
    timestamp = models.DateTimeField(null=True, blank=True)
    author = models.CharField(max_length=100, null=True, blank=True)
    duration = models.PositiveIntegerField(null=True, blank=True)
    filesize = models.PositiveIntegerField(null=True, blank=True)
    language = models.CharField(max_length=10, null=True, blank=True)
    last_update = models.DateTimeField(auto_now=True)
    outdated = models.BooleanField(default=False) #set to true after episode hasn't been found in feed
    mimetype = models.CharField(max_length=30, blank=True, null=True)

    def number(self):
        m = re.search('\D*(\d+)\D+', self.title)
        return m.group(1) if m else ''

    def shortname(self):
        s = self.title
        s = s.replace(self.podcast.title, '')
        s = s.replace(self.number(), '')
        m = re.search('\W*(.+)', s)
        s = m.group(1) if m else s
        s = s.strip()
        return s

    def __unicode__(self):
        return '%s (%s)' % (self.shortname(), self.podcast)

    class Meta:
        db_table = 'episode'
        unique_together = ('podcast', 'url')


class SyncGroup(models.Model):
    """
    Devices that should be synced with each other need to be grouped
    in a SyncGroup.

    SyncGroups are automatically created by calling
    device.sync_with(other_device), but can also be created manually.

    device.sync() synchronizes the device for which the method is called
    with the other devices in its SyncGroup.
    """
    user = models.ForeignKey(User)

    def __unicode__(self):
        devices = [d.name for d in Device.objects.filter(sync_group=self)]
        return ', '.join(devices)

    def devices(self):
        return Device.objects.filter(sync_group=self)

    def add(self, device):
        if device.sync_group == self: return
        if device.sync_group != None:
            device.unsync()

        device.sync_group = self
        device.save()

    class Meta:
        db_table = 'sync_group'


class Device(models.Model):
    user = models.ForeignKey(User)
    uid = models.SlugField(max_length=50)
    name = models.CharField(max_length=100, blank=True, default='Default Device')
    type = models.CharField(max_length=10, choices=DEVICE_TYPES, default='other')
    sync_group = models.ForeignKey(SyncGroup, blank=True, null=True)
    deleted = models.BooleanField(default=False)
    settings = JSONField(default={})

    def __unicode__(self):
        return self.name if self.name else _('Unnamed Device (%s)' % self.uid)


    class Meta:
        db_table = 'device'



class EpisodeAction(models.Model):
    user = models.ForeignKey(User)
    episode = models.ForeignKey(Episode)
    device = models.ForeignKey(Device,null=True)
    action = models.CharField(max_length=10, choices=EPISODE_ACTION_TYPES)
    timestamp = models.DateTimeField(default=datetime.now)
    started = models.IntegerField(null=True, blank=True)
    playmark = models.IntegerField(null=True, blank=True)
    total = models.IntegerField(null=True, blank=True)

    def __unicode__(self):
        return '%s %s %s' % (self.user, self.action, self.episode)

    def playmark_time(self):
        try:
            return datetime.fromtimestamp(float(self.playmark))
        except ValueError:
            return 0

    def started_time(self):
        try:
            return datetime.fromtimestamp(float(self.started))
        except ValueError:
            return 0

    class Meta:
        db_table = 'episode_log'


# deprecated, only used in migration code
class SubscriptionMeta(models.Model):
    user = models.ForeignKey(User)
    podcast = models.ForeignKey(Podcast)
    public = models.BooleanField(default=True)
    settings = JSONField(default={})

    def __unicode__(self):
        return '%s - %s - %s' % (self.user, self.podcast, self.public)

    def save(self, *args, **kwargs):
        self.public = self.settings.get('public_subscription', True)
        super(SubscriptionMeta, self).save(*args, **kwargs)


    class Meta:
        db_table = 'subscription'
        unique_together = ('user', 'podcast')


# deprecated, only used in migration code
class SubscriptionAction(models.Model):
    device = models.ForeignKey(Device)
    podcast = models.ForeignKey(Podcast)
    action = models.IntegerField(choices=SUBSCRIPTION_ACTION_TYPES)
    timestamp = models.DateTimeField(blank=True, default=datetime.now)

    def action_string(self):
        return 'subscribe' if self.action == SUBSCRIBE_ACTION else 'unsubscribe'

    def newer_than(self, action):
        return self.timestamp > action.timestamp

    def __unicode__(self):
        return '%s %s %s %s' % (self.device.user, self.device, self.action_string(), self.podcast)

    class Meta:
        db_table = 'subscription_log'
        unique_together = ('device', 'podcast', 'timestamp')


from django.db.models.signals import post_save, pre_delete
from mygpo.migrate import save_podcast_signal, delete_podcast_signal, save_episode_signal, delete_episode_signal, save_device_signal, delete_device_signal

post_save.connect(save_podcast_signal, sender=Podcast)
pre_delete.connect(delete_podcast_signal, sender=Podcast)

post_save.connect(save_episode_signal, sender=Episode)
pre_delete.connect(delete_episode_signal, sender=Episode)
