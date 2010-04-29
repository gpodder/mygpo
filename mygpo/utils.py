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

def daterange(from_date, to_date=datetime.now(), leap=timedelta(days=1)):
    while from_date <= to_date:
        yield from_date
        from_date = from_date + leap
    return

def format_time(value):
    """Format an offset (in seconds) to a string

    The offset should be an integer or float value.

    >>> format_time(0)
    '00:00:00'
    >>> format_time(20)
    '00:00:20'
    >>> format_time(3600)
    '01:00:00'
    >>> format_time(10921)
    '03:02:01'
    """
    dt = datetime.utcfromtimestamp(value)
    return dt.strftime('%H:%M:%S')

def parse_time(value):
    if value is None:
        raise ValueError('None value in parse_time')

    if isinstance(value, int):
        # Don't need to parse already-converted time value
        return value

    if value == '':
        raise ValueError('Empty valueing in parse_time')

    for format in ('%H:%M:%S', '%M:%S'):
        try:
            t = time.strptime(value, format)
            return t.tm_hour * 60*60 + t.tm_min * 60 + t.tm_sec
        except ValueError, e:
            continue

    return int(value)

