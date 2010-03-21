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

from datetime import datetime, timedelta, time
import time

def daterange(from_date, to_date=datetime.now()):
    while from_date <= to_date:
        yield from_date
        from_date = from_date + timedelta(days=1)
    return


def parse_time(str):
    if not str:
        raise ValueError('can\'t parse empty string')

    for format in ('%H:%M:%S', '%M:%S'):
        try:
            t = time.strptime(str, format)
            return t.tm_hour * 60*60 + t.tm_min * 60 + t.tm_sec
        except ValueError, e:
            continue

    return int(str)

