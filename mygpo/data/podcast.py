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

from mygpo.api.models import Podcast, Episode

def avg_update_interval(podcast):
    """
    returns the average interval between episodes for a given podcast
    """
    unique_timestamps = Episode.objects.filter(podcast=p, timestamp__isnull=False).order_by('timestamp').values('timestamp').distinct()
    c = unique_timestamps.count()
    t1 = unique_timestamps[0]['timestamp']
    t2 = unique_timestamps[c-1]['timestamp']
    return max(1, (t2 - t1).days / c)

