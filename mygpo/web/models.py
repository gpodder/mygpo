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

class Rating(models.Model):
    target = models.CharField(max_length=15)
    user = models.ForeignKey(User)
    rating = models.IntegerField()
    timestamp = models.DateTimeField(default=datetime.now)

    class Meta:
        db_table = 'ratings'

    def __unicode__(self):
        return '%s rates %s as %s on %s' % (self.user, self.target, self.rating, self.timestamp)


class SecurityToken(models.Model):
    user = models.ForeignKey(User)
    token = models.CharField(max_length=32, blank=True)
    object = models.CharField(max_length=64)
    action = models.CharField(max_length=10)

    class Meta:
        db_table = 'security_tokens'

    def __unicode__(self):
        return '%s %s %s: %s' % (self.user, self.object, self.action, self.token[:5])


