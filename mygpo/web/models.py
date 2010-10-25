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
from mygpo.api.models import Podcast
from datetime import datetime
import random
import string


# Deprecated: only used in migration-code anymore
class Rating(models.Model):
    target = models.CharField(max_length=15)
    user = models.ForeignKey(User)
    rating = models.IntegerField()
    timestamp = models.DateTimeField(default=datetime.now)

    class Meta:
        db_table = 'ratings'
        managed = False

    def __unicode__(self):
        return '%s rates %s as %s on %s' % (self.user, self.target, self.rating, self.timestamp)


class SecurityToken(models.Model):
    user = models.ForeignKey(User)
    token = models.CharField(max_length=32, blank=True, default=lambda: "".join(random.sample(string.letters+string.digits, 32)))
    object = models.CharField(max_length=64)
    action = models.CharField(max_length=10)

    class Meta:
        db_table = 'security_tokens'
        managed = False

    def __unicode__(self):
        return '%s %s %s: %s' % (self.user, self.object, self.action, self.token[:5])

    def random_token(self, length=32):
        self.token = "".join(random.sample(string.letters+string.digits, length))

    def check(self, token):
        if self.token == '':
            return True
        return self.token == token


class Advertisement(models.Model):
    podcast = models.ForeignKey(Podcast)
    title = models.CharField(max_length=100)
    text = models.TextField()
    start = models.DateTimeField()
    end = models.DateTimeField()

    class Meta:
        db_table = 'advertisements'
        managed = False

    def __unicode__(self):
        return '%s (%s - %s)' % (self.podcast, self.start, self.end)

