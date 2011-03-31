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
from mygpo.api.models import Episode, Device
from datetime import datetime
from mygpo import migrate

# deprecated, only used in migration code anymore
class Chapter(models.Model):
    user = models.ForeignKey(User)
    episode = models.ForeignKey(Episode)
    device = models.ForeignKey(Device, null=True)
    created = models.DateTimeField(default=datetime.now)
    start = models.IntegerField()
    end = models.IntegerField()
    label = models.CharField(max_length=50, blank=True)
    advertisement = models.BooleanField(default=False)

    class Meta:
        db_table = 'chapters'
        managed = False

