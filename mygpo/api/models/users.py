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
from mygpo.api.models import Episode

class EpisodeFavorite(models.Model):
    user = models.ForeignKey(User)
    episode = models.ForeignKey(Episode)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'episode_favorites'
        unique_together = ('user', 'episode')
        managed = False

