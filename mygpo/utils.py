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

import sys
import collections
from datetime import datetime, timedelta, date
import time

def daterange(from_date, to_date=None, leap=timedelta(days=1)):
    """
    >>> from_d = datetime(2010, 01, 01)
    >>> to_d = datetime(2010, 01, 05)
    >>> list(daterange(from_d, to_d))
    [datetime.datetime(2010, 1, 1, 0, 0), datetime.datetime(2010, 1, 2, 0, 0), datetime.datetime(2010, 1, 3, 0, 0), datetime.datetime(2010, 1, 4, 0, 0), datetime.datetime(2010, 1, 5, 0, 0)]
    """

    if to_date is None:
        if isinstance(from_date, datetime):
            to_date = datetime.now()
        else:
            to_date = date.today()

    while from_date <= to_date:
        yield from_date
        from_date = from_date + leap
    return

def format_time(value):
    """Format an offset (in seconds) to a string

    The offset should be an integer or float value.

    >>> format_time(0)
    '00:00'
    >>> format_time(20)
    '00:20'
    >>> format_time(3600)
    '01:00:00'
    >>> format_time(10921)
    '03:02:01'
    """
    try:
        dt = datetime.utcfromtimestamp(value)
    except ValueError:
        return ''

    if dt.hour == 0:
        return dt.strftime('%M:%S')
    else:
        return dt.strftime('%H:%M:%S')

def parse_time(value):
    """
    >>> parse_time(10)
    10

    >>> parse_time('05:10') #5*60+10
    310

    >>> parse_time('1:05:10') #60*60+5*60+10
    3910
    """
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


def parse_bool(val):
    """
    >>> parse_bool('True')
    True

    >>> parse_bool('true')
    True

    >>> parse_bool('')
    False
    """
    if isinstance(val, bool):
        return val
    if val.lower() == 'true':
        return True
    return False


def iterate_together(l1, l2, compare=lambda x, y: cmp(x, y)):
    """
    takes two ordered, possible sparse, lists l1 and l2 with similar items
    (some items have a corresponding item in the other list, some don't).

    It then yield tuples of corresponding items, where one element is None is
    there is no corresponding entry in one of the lists.

    Tuples where both elements are None are skipped.

    compare is a method for comparing items from both lists; it defaults
    to cmp.

    >>> list(iterate_together(range(1, 3), range(1, 4, 2)))
    [(1, 1), (2, None), (None, 3)]

    >>> list(iterate_together([], []))
    []

    >>> list(iterate_together(range(1, 3), range(3, 5)))
    [(1, None), (2, None), (None, 3), (None, 4)]

    >>> list(iterate_together(range(1, 3), []))
    [(1, None), (2, None)]

    >>> list(iterate_together([1, None, 3], [None, None, 3]))
    [(1, None), (3, 3)]
    """

    l1 = iter(l1)
    l2 = iter(l2)

    def _take(it):
        try:
            i = it.next()
            while i is None:
                i = it.next()
            return i, True
        except StopIteration:
            return None, False

    i1, more1 = _take(l1)
    i2, more2 = _take(l2)

    while more1 or more2:
        if not more2 or (i1 is not None and compare(i1, i2) < 0):
            yield(i1, None)
            i1, more1 = _take(l1)

        elif not more1 or (i2 is not None and compare(i1, i2) > 0):
            yield(None, i2)
            i2, more2 = _take(l2)

        elif compare(i1, i2) == 0:
            yield(i1, i2)
            i1, more1 = _take(l1)
            i2, more2 = _take(l2)


def progress(val, max_val, status_str='', max_width=50, stream=sys.stdout):
    print >> stream, '\r',
    print >> stream, '[ %s ] %s / %s | %s' % (
        '#'*int(float(val)/max_val*max_width) +
        ' ' * (max_width-(int(float(val)/max_val*max_width))),
        val,
        max_val,
        status_str),
    stream.flush()


def set_by_frequency(l):
    """
    Creates a set from all items in l and returns it as a list in which the
    items are ordered by decreasing number of occurance in the original list

    >>> set_by_frequency([1, 2, 1, 2, 1, 3])
    [1, 2, 3]

    >>> set_by_frequency([1, 1, 1, 2])
    [1, 2]

    >>> set_by_frequency([])
    []
    """
    d = collections.defaultdict(int)
    for i in l:
        d[i] += + 1
    l = sorted(d.items(), key=lambda(i, c): c, reverse=True)
    return [i for (i, c) in l]


def set_cmp(list, simplify):
    """
    Builds a set out of a list but uses the results of simplify to determine equality between items
    """
    simpl = lambda x: (simplify(x), x)
    lst = dict(map(simpl, list))
    return lst.values()


def first(it):
    """
    returns the first not-None object or None if the iterator is exhausted
    """
    for x in it:
        if x != None:
            return x
    return None


def intersect(a, b):
     return list(set(a) & set(b))


def multi_request_view(cls, view, *args, **kwargs):
    """
    splits up a view request into several requests, which reduces
    the server load of the number of returned objects is large.

    NOTE: As such a split request is obviously not atomical anymore, results
    might skip some elements of contain some twice
    """

    LIMIT = 1000
    cur = 0

    while True:
        resp = cls.view(view, *args, skip=cur, limit=LIMIT, **kwargs)
        if resp.count() == 0:
            break
        for obj in resp.iterator():
            yield obj

        cur += LIMIT


def remove_control_chars(s):
    import unicodedata, re

    all_chars = (unichr(i) for i in xrange(0x110000))
    control_chars = ''.join(map(unichr, range(0,32) + range(127,160)))
    control_char_re = re.compile('[%s]' % re.escape(control_chars))

    return control_char_re.sub('', s)


def unzip(a):
    return tuple(map(list,zip(*a)))


def parse_range(s, min, max, default=None):
    """
    Parses the string and returns its value. If the value is outside the given
    range, its closest number within the range is returned

    >>> parse_range('5', 0, 10)
    5

    >>> parse_range('0', 5, 10)
    5

    >>> parse_range('15',0, 10)
    10

    >>> parse_range('x', 0, 20)
    10

    >>> parse_range('x', 0, 20, 20)
    20
    """
    try:
        val = int(s)
        if val < min:
            return min
        if val > max:
            return max
        return val

    except ValueError:
        return default if default is not None else (max-min)/2


def get_to_dict(cls, ids):
    ids = list(set(ids))
    objs = cls.get_multi(ids)
    return dict(zip(ids, objs))


def flatten(l):
    return [item for sublist in l for item in sublist]


def linearize(key, iterators, reverse=False):
    """
    Linearizes a number of iterators, sorted by some comparison function
    """

    iters = [iter(i) for i in iterators]
    vals = []
    for i in iters:
        try:
            v = i.next()
            vals. append( (v, i) )
        except StopIteration:
            continue

    while vals:
        vals = sorted(vals, key=lambda x: key(x[0]), reverse=reverse)
        val, it = vals.pop(0)
        yield val
        try:
            next_val = it.next()
            vals.append( (next_val, it) )
        except StopIteration:
            pass


def skip_pairs(iterator, cmp=cmp):
    """ Skips pairs of equal items

    >>> list(skip_pairs([]))
    []

    >>> list(skip_pairs([1]))
    [1]

    >>> list(skip_pairs([1, 2, 3]))
    [1, 2, 3]

    >>> list(skip_pairs([1, 1]))
    []

    >>> list(skip_pairs([1, 2, 2]))
    [1]

    >>> list(skip_pairs([1, 2, 2, 3]))
    [1, 3]

    >>> list(skip_pairs([1, 2, 2, 2]))
    [1, 2]

    >>> list(skip_pairs([1, 2, 2, 2, 2, 3]))
    [1, 3]
    """

    iterator = iter(iterator)
    next = iterator.next()

    while True:
        item = next
        try:
            next = iterator.next()
        except StopIteration as e:
            yield item
            raise e

        if cmp(item, next) == 0:
            next = iterator.next()
        else:
            yield item
