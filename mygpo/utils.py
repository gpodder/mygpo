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
import hashlib
import urlparse
import urllib
import urllib2

from django.conf import settings


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

    # progress as percentage
    percentage_str = '{val:.2%}'.format(val=float(val)/max_val)

    # progress bar filled with #s
    progress_str = '#'*int(float(val)/max_val*max_width) + \
                   ' ' * (max_width-(int(float(val)/max_val*max_width)))

    #insert percentage into bar
    percentage_start = int((max_width-len(percentage_str))/2)
    progress_str = progress_str[:percentage_start] + \
                   percentage_str + \
                   progress_str[percentage_start+len(percentage_str):]

    print >> stream, '\r',
    print >> stream, '[ %s ] %s / %s | %s' % (
        progress_str,
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



def additional_value(it, gen_val, val_changed=lambda _: True):
    """ Provides an additional value to the elements, calculated when needed

    For the elements from the iterator, some additional value can be computed
    by gen_val (which might be an expensive computation).

    If the elements in the iterator are ordered so that some subsequent
    elements would generate the same additional value, val_changed can be
    provided, which receives the next element from the iterator and the
    previous additional value. If the element would generate the same
    additional value (val_changed returns False), its computation is skipped.

    >>> # get the next full hundred higher than x
    >>> # this will probably be an expensive calculation
    >>> next_hundred = lambda x: x + 100-(x % 100)

    >>> # returns True if h is not the value that next_hundred(x) would provide
    >>> # this should be a relatively cheap calculation, compared to the above
    >>> diff_hundred = lambda x, h: (h-x) < 0 or (h - x) > 100

    >>> xs = [0, 50, 100, 101, 199, 200, 201]
    >>> list(additional_value(xs, next_hundred, diff_hundred))
    [(0, 100), (50, 100), (100, 100), (101, 200), (199, 200), (200, 200), (201, 300)]
    """

    _none = object()
    current = _none

    for x in it:
        if current is _none or val_changed(x, current):
            current = gen_val(x)

        yield (x, current)


def file_hash(f, h=hashlib.md5, block_size=2**20):
    """ returns the hash of the contents of a file """
    f_hash = h()
    for chunk in iter(lambda: f.read(block_size), ''):
         f_hash.update(chunk)
    return f_hash



def split_list(l, prop):
    """ split elements that satisfy a property, and those that don't """
    match   = filter(prop, l)
    nomatch = [x for x in l if x not in match]
    return match, nomatch


def url_add_authentication(url, username, password):
    """
    Adds authentication data (username, password) to a given
    URL in order to construct an authenticated URL.

    >>> url_add_authentication('https://host.com/', '', None)
    'https://host.com/'
    >>> url_add_authentication('http://example.org/', None, None)
    'http://example.org/'
    >>> url_add_authentication('telnet://host.com/', 'foo', 'bar')
    'telnet://foo:bar@host.com/'
    >>> url_add_authentication('ftp://example.org', 'billy', None)
    'ftp://billy@example.org'
    >>> url_add_authentication('ftp://example.org', 'billy', '')
    'ftp://billy:@example.org'
    >>> url_add_authentication('http://localhost/x', 'aa', 'bc')
    'http://aa:bc@localhost/x'
    >>> url_add_authentication('http://blubb.lan/u.html', 'i/o', 'P@ss:')
    'http://i%2Fo:P@ss:@blubb.lan/u.html'
    >>> url_add_authentication('http://a:b@x.org/', 'c', 'd')
    'http://c:d@x.org/'
    >>> url_add_authentication('http://i%2F:P%40%3A@cx.lan', 'P@x', 'i/')
    'http://P@x:i%2F@cx.lan'
    >>> url_add_authentication('http://x.org/', 'a b', 'c d')
    'http://a%20b:c%20d@x.org/'
    """
    if username is None or username == '':
        return url

    # Relaxations of the strict quoting rules (bug 1521):
    # 1. Accept '@' in username and password
    # 2. Acecpt ':' in password only
    username = urllib.quote(username, safe='@')

    if password is not None:
        password = urllib.quote(password, safe='@:')
        auth_string = ':'.join((username, password))
    else:
        auth_string = username

    url = url_strip_authentication(url)

    url_parts = list(urlparse.urlsplit(url))
    # url_parts[1] is the HOST part of the URL
    url_parts[1] = '@'.join((auth_string, url_parts[1]))

    return urlparse.urlunsplit(url_parts)


def urlopen(url, headers=None, data=None):
    """
    An URL opener with the User-agent set to gPodder (with version)
    """
    username, password = username_password_from_url(url)
    if username is not None or password is not None:
        url = url_strip_authentication(url)
        password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, url, username, password)
        handler = urllib2.HTTPBasicAuthHandler(password_mgr)
        opener = urllib2.build_opener(handler)
    else:
        opener = urllib2.build_opener()

    if headers is None:
        headers = {}
    else:
        headers = dict(headers)

    headers.update({'User-agent': settings.USER_AGENT})
    request = urllib2.Request(url, data=data, headers=headers)
    return opener.open(request)



def username_password_from_url(url):
    r"""
    Returns a tuple (username,password) containing authentication
    data from the specified URL or (None,None) if no authentication
    data can be found in the URL.

    See Section 3.1 of RFC 1738 (http://www.ietf.org/rfc/rfc1738.txt)

    >>> username_password_from_url('https://@host.com/')
    ('', None)
    >>> username_password_from_url('telnet://host.com/')
    (None, None)
    >>> username_password_from_url('ftp://foo:@host.com/')
    ('foo', '')
    >>> username_password_from_url('http://a:b@host.com/')
    ('a', 'b')
    >>> username_password_from_url(1)
    Traceback (most recent call last):
      ...
    ValueError: URL has to be a string or unicode object.
    >>> username_password_from_url(None)
    Traceback (most recent call last):
      ...
    ValueError: URL has to be a string or unicode object.
    >>> username_password_from_url('http://a@b:c@host.com/')
    ('a@b', 'c')
    >>> username_password_from_url('ftp://a:b:c@host.com/')
    ('a', 'b:c')
    >>> username_password_from_url('http://i%2Fo:P%40ss%3A@host.com/')
    ('i/o', 'P@ss:')
    >>> username_password_from_url('ftp://%C3%B6sterreich@host.com/')
    ('\xc3\xb6sterreich', None)
    >>> username_password_from_url('http://w%20x:y%20z@example.org/')
    ('w x', 'y z')
    >>> username_password_from_url('http://example.com/x@y:z@test.com/')
    (None, None)
    """
    if type(url) not in (str, unicode):
        raise ValueError('URL has to be a string or unicode object.')

    (username, password) = (None, None)

    (scheme, netloc, path, params, query, fragment) = urlparse.urlparse(url)

    if '@' in netloc:
        (authentication, netloc) = netloc.rsplit('@', 1)
        if ':' in authentication:
            (username, password) = authentication.split(':', 1)

            # RFC1738 dictates that we should not allow ['/', '@', ':']
            # characters in the username and password field (Section 3.1):
            #
            # 1. The "/" can't be in there at this point because of the way
            #    urlparse (which we use above) works.
            # 2. Due to gPodder bug 1521, we allow "@" in the username and
            #    password field. We use netloc.rsplit('@', 1), which will
            #    make sure that we split it at the last '@' in netloc.
            # 3. The colon must be excluded (RFC2617, Section 2) in the
            #    username, but is apparently allowed in the password. This
            #    is handled by the authentication.split(':', 1) above, and
            #    will cause any extraneous ':'s to be part of the password.

            username = urllib.unquote(username)
            password = urllib.unquote(password)
        else:
            username = urllib.unquote(authentication)

    return (username, password)


def url_strip_authentication(url):
    """
    Strips authentication data from an URL. Returns the URL with
    the authentication data removed from it.

    >>> url_strip_authentication('https://host.com/')
    'https://host.com/'
    >>> url_strip_authentication('telnet://foo:bar@host.com/')
    'telnet://host.com/'
    >>> url_strip_authentication('ftp://billy@example.org')
    'ftp://example.org'
    >>> url_strip_authentication('ftp://billy:@example.org')
    'ftp://example.org'
    >>> url_strip_authentication('http://aa:bc@localhost/x')
    'http://localhost/x'
    >>> url_strip_authentication('http://i%2Fo:P%40ss%3A@blubb.lan/u.html')
    'http://blubb.lan/u.html'
    >>> url_strip_authentication('http://c:d@x.org/')
    'http://x.org/'
    >>> url_strip_authentication('http://P%40%3A:i%2F@cx.lan')
    'http://cx.lan'
    >>> url_strip_authentication('http://x@x.com:s3cret@example.com/')
    'http://example.com/'
    """
    url_parts = list(urlparse.urlsplit(url))
    # url_parts[1] is the HOST part of the URL

    # Remove existing authentication data
    if '@' in url_parts[1]:
        url_parts[1] = url_parts[1].rsplit('@', 1)[1]

    return urlparse.urlunsplit(url_parts)


def sanitize_encoding(filename):
    r"""
    Generate a sanitized version of a string (i.e.
    remove invalid characters and encode in the
    detected native language encoding).

    >>> sanitize_encoding('\x80')
    ''
    >>> sanitize_encoding(u'unicode')
    'unicode'
    """
    # The encoding problem goes away in Python 3.. hopefully!
    if sys.version_info >= (3, 0):
        return filename

    global encoding
    if not isinstance(filename, unicode):
        filename = filename.decode(encoding, 'ignore')
    return filename.encode(encoding, 'ignore')
