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

import operator
import sys
import re
import collections
from datetime import datetime, timedelta, date
import time

from django.core.cache import cache


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


def iterate_together(lists, key=lambda x: x, reverse=False):
    """
    takes ordered, possibly sparse, lists with similar items
    (some items have a corresponding item in the other lists, some don't).

    It then yield tuples of corresponding items, where one element is None is
    there is no corresponding entry in one of the lists.

    Tuples where both elements are None are skipped.

    The results of the key method are used for the comparisons.

    If reverse is True, the lists are expected to be sorted in reverse order
    and the results will also be sorted reverse

    >>> list(iterate_together([range(1, 3), range(1, 4, 2)]))
    [(1, 1), (2, None), (None, 3)]

    >>> list(iterate_together([[], []]))
    []

    >>> list(iterate_together([range(1, 3), range(3, 5)]))
    [(1, None), (2, None), (None, 3), (None, 4)]

    >>> list(iterate_together([range(1, 3), []]))
    [(1, None), (2, None)]

    >>> list(iterate_together([[1, None, 3], [None, None, 3]]))
    [(1, None), (3, 3)]
    """

    Next = collections.namedtuple('Next', 'item more')
    min_ = min if not reverse else max
    lt_  = operator.lt if not reverse else operator.gt

    lists = [iter(l) for l in lists]

    def _take(it):
        try:
            i = it.next()
            while i is None:
                i = it.next()
            return Next(i, True)
        except StopIteration:
            return Next(None, False)

    def new_res():
        return [None]*len(lists)

    # take first bunch of items
    items = [_take(l) for l in lists]

    while any(i.item is not None or i.more for i in items):

        res = new_res()

        for n, item in enumerate(items):

            if item.item is None:
                continue

            if all(x is None for x in res):
                res[n] = item.item
                continue

            min_v = min_(filter(lambda x: x is not None, res), key=key)

            if key(item.item) == key(min_v):
                res[n] = item.item

            elif lt_(key(item.item), key(min_v)):
                res = new_res()
                res[n] = item.item

        for n, x in enumerate(res):
            if x is not None:
                items[n] = _take(lists[n])

        yield tuple(res)


def progress(val, max_val, status_str='', max_width=50, stream=sys.stdout):
    print >> stream, '\r',
    print >> stream, '[ %s ] %s / %s | %s' % (
        '#'*int(float(val)/max_val*max_width) +
        ' ' * (max_width-(int(float(val)/max_val*max_width))),
        val,
        max_val,
        status_str),
    stream.flush()


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


def multi_request_view(cls, view, wrap=True, *args, **kwargs):
    """
    splits up a view request into several requests, which reduces
    the server load of the number of returned objects is large.

    NOTE: As such a split request is obviously not atomical anymore, results
    might skip some elements of contain some twice
    """

    per_page = kwargs.get('limit', 1000)
    kwargs['limit'] = per_page + 1
    db = cls.get_db()
    cont = True

    while cont:

        resp = db.view(view, *args, **kwargs)
        cont = False

        for n, obj in enumerate(resp.iterator()):

            key = obj['key']

            if wrap:
                doc = cls.wrap(obj['doc'])
                docid = doc._id
            else:
                docid = obj['id']
                doc = obj

            if n == per_page:
                kwargs['startkey'] = key
                kwargs['startkey_docid'] = docid
                if 'skip' in kwargs:
                    del kwargs['skip']

                # we reached the end of the page, load next one
                cont = True
                break

            yield doc


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

    except (ValueError, TypeError):
        return default if default is not None else (max-min)/2


def get_to_dict(cls, ids, get_id=lambda x: x._id, use_cache=False):

    ids = list(set(ids))
    objs = dict()

    cache_objs = []
    if use_cache:
        for id in ids:
            obj = cache.get(id)
            if obj is not None:
                cache_objs.append(obj)
                ids.remove(id)

    db_objs = list(cls.get_multi(ids))

    if use_cache:
        for obj in db_objs:
            cache.set(get_id(obj), obj)

    return dict((get_id(obj), obj) for obj in cache_objs + db_objs)


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


def get_timestamp(datetime_obj):
    """ Returns the timestamp as an int for the given datetime object

    >>> get_timestamp(datetime(2011, 4, 7, 9, 30, 6))
    1302168606

    >>> get_timestamp(datetime(1970, 1, 1, 0, 0, 0))
    0
    """
    return int(time.mktime(datetime_obj.timetuple()))



re_url = re.compile('^https?://')

def is_url(string):
    """ Returns true if a string looks like an URL

    >>> is_url('http://example.com/some-path/file.xml')
    True

    >>> is_url('something else')
    False
    """

    return bool(re_url.match(string))


def is_couchdb_id(id_str):
    import string
    import operator
    import functools
    f = functools.partial(operator.contains, string.hexdigits)
    return len(id_str) == 32 and all(map(f, id_str))


# from http://stackoverflow.com/questions/2892931/longest-common-substring-from-more-than-two-strings-python
# this does not increase asymptotical complexity
# but can still waste more time than it saves.
def shortest_of(strings):
    return min(strings, key=len)

def longest_substr(strings):
    """
    Returns the longest common substring of the given strings
    """

    substr = ""
    if not strings:
        return substr
    reference = shortest_of(strings) #strings[0]
    length = len(reference)
    #find a suitable slice i:j
    for i in xrange(length):
        #only consider strings long at least len(substr) + 1
        for j in xrange(i + len(substr) + 1, length):
            candidate = reference[i:j]
            if all(candidate in text for text in strings):
                substr = candidate
    return substr
