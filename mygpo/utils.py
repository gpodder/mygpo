# -*- coding: utf-8 -*-
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

import json
import functools
import types
import subprocess
import os
import operator
import sys
import re
import collections
import itertools
from datetime import datetime, timedelta, date
import time
import hashlib
import urllib.parse
import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
import zlib
import shlex

from django.db import transaction, IntegrityError
from django.conf import settings
from django.core.urlresolvers import reverse

import logging
logger = logging.getLogger(__name__)


def daterange(from_date, to_date=None, leap=timedelta(days=1)):
    """
    >>> from_d = datetime(2010, 1, 1)
    >>> to_d = datetime(2010, 1, 5)
    >>> list(daterange(from_d, to_d))
    [datetime.datetime(2010, 1, 1, 0, 0), datetime.datetime(2010, 1, 2, 0, 0), datetime.datetime(2010, 1, 3, 0, 0), datetime.datetime(2010, 1, 4, 0, 0), datetime.datetime(2010, 1, 5, 0, 0)]
    """

    if to_date is None:
        if isinstance(from_date, datetime):
            to_date = datetime.utcnow()
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
    except (ValueError, TypeError):
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
        except ValueError as e:
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
            i = next(it)
            while i is None:
                i = next(it)
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

    factor = float(val)/max_val if max_val > 0 else 0

    # progress as percentage
    percentage_str = '{val:.2%}'.format(val=factor)

    # progress bar filled with #s
    factor = min(int(factor*max_width), max_width)
    progress_str = '#' * factor + ' ' * (max_width-factor)

    #insert percentage into bar
    percentage_start = int((max_width-len(percentage_str))/2)
    progress_str = progress_str[:percentage_start] + \
                   percentage_str + \
                   progress_str[percentage_start+len(percentage_str):]

    print('\r', end=' ', file=stream)
    print('[ %s ] %s / %s | %s' % (
        progress_str,
        val,
        max_val,
        status_str), end=' ', file=stream)
    stream.flush()


def set_cmp(list, simplify):
    """
    Builds a set out of a list but uses the results of simplify to determine equality between items
    """
    simpl = lambda x: (simplify(x), x)
    lst = dict(map(simpl, list))
    return list(lst.values())


def first(it):
    """
    returns the first not-None object or None if the iterator is exhausted
    """
    for x in it:
        if x is not None:
            return x
    return None


def intersect(a, b):
    return list(set(a) & set(b))



def remove_control_chars(s):
    all_chars = (chr(i) for i in range(0x110000))
    control_chars = ''.join(map(chr, list(range(0,32)) + list(range(127,160))))
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

    >>> parse_range('0', 5.0, 10)
    5.0

    >>> parse_range('15',0, 10)
    10

    >>> parse_range('x', 0., 20)
    10.0

    >>> parse_range('x', 0, 20, 20)
    20
    """
    out_type = type(min)

    try:
        val = int(s)
        if val < min:
            return min
        if val > max:
            return max
        return val

    except (ValueError, TypeError):
        return default if default is not None else out_type((max-min)/2)



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
            v = next(i)
            vals. append( (v, i) )
        except StopIteration:
            continue

    while vals:
        vals = sorted(vals, key=lambda x: key(x[0]), reverse=reverse)
        val, it = vals.pop(0)
        yield val
        try:
            next_val = next(it)
            vals.append( (next_val, it) )
        except StopIteration:
            pass


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
    reference = shortest_of(strings)
    length = len(reference)
    #find a suitable slice i:j
    for i in range(length):
        #only consider strings long at least len(substr) + 1
        for j in range(i + len(substr) + 1, length):
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
    while True:
        buf = f.read(block_size)
        if not buf:
            break
        f_hash.update( buf )

    return f_hash


def split_list(l, prop):
    """ split elements that satisfy a property, and those that don't """
    match   = list(filter(prop, l))
    nomatch = [x for x in l if x not in match]
    return match, nomatch


def sorted_chain(links, key, reverse=False):
    """ Takes a list of iters can iterates over sorted elements

    Each elment of links should be a tuple of (sort_key, iterator). The
    elements of each iterator should be sorted already. sort_key should
    indicate the key of the first element and needs to be comparable to the
    result of key(elem).

    The function returns an iterator over the globally sorted element that
    ensures that as little iterators as possible are evaluated.  When
    evaluating """

    # mixed_list initially contains all placeholders; later evaluated
    # elements (from the iterators) are mixed in
    mixed_list = [(k, link, True) for k, link in links]

    while mixed_list:
        _, item, expand = mixed_list.pop(0)

        # found an element (from an earlier expansion), yield it
        if not expand:
            yield item
            continue

        # found an iter that needs to be expanded.
        # The iterator is fully consumed
        new_items = [(key(i), i, False) for i in item]

        # sort links (placeholders) and elements together
        mixed_list = sorted(mixed_list + new_items, key=lambda t: t[0],
                reverse=reverse)


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
    username = urllib.parse.quote(username, safe='@')

    if password is not None:
        password = urllib.parse.quote(password, safe='@:')
        auth_string = ':'.join((username, password))
    else:
        auth_string = username

    url = url_strip_authentication(url)

    url_parts = list(urllib.parse.urlsplit(url))
    # url_parts[1] is the HOST part of the URL
    url_parts[1] = '@'.join((auth_string, url_parts[1]))

    return urllib.parse.urlunsplit(url_parts)


def urlopen(url, headers=None, data=None):
    """
    An URL opener with the User-agent set to gPodder (with version)
    """
    username, password = username_password_from_url(url)
    if username is not None or password is not None:
        url = url_strip_authentication(url)
        password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, url, username, password)
        handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
        opener = urllib.request.build_opener(handler)
    else:
        opener = urllib.request.build_opener()

    if headers is None:
        headers = {}
    else:
        headers = dict(headers)

    headers.update({'User-agent': settings.USER_AGENT})
    request = urllib.request.Request(url, data=data, headers=headers)
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
    ('österreich', None)
    >>> username_password_from_url('http://w%20x:y%20z@example.org/')
    ('w x', 'y z')
    >>> username_password_from_url('http://example.com/x@y:z@test.com/')
    (None, None)
    """
    if type(url) not in (str, str):
        raise ValueError('URL has to be a string or unicode object.')

    (username, password) = (None, None)

    (scheme, netloc, path, params, query, fragment) = urllib.parse.urlparse(url)

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

            username = urllib.parse.unquote(username)
            password = urllib.parse.unquote(password)
        else:
            username = urllib.parse.unquote(authentication)

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
    url_parts = list(urllib.parse.urlsplit(url))
    # url_parts[1] is the HOST part of the URL

    # Remove existing authentication data
    if '@' in url_parts[1]:
        url_parts[1] = url_parts[1].rsplit('@', 1)[1]

    return urllib.parse.urlunsplit(url_parts)


# Native filesystem encoding detection
encoding = sys.getfilesystemencoding()


def get_git_head():
    """ returns the commit and message of the current git HEAD """

    try:
        pr = subprocess.Popen('/usr/bin/git log -n 1 --oneline'.split(),
            cwd = settings.BASE_DIR,
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
        )

    except OSError:
        return None, None

    (out, err) = pr.communicate()
    if err:
        return None, None

    outs = [o.decode('utf-8') for o in out.split()]
    commit = outs[0]
    msg = ' ' .join(outs[1:])
    return commit, msg


def parse_request_body(request):
    """ returns the parsed request body, handles gzip encoding """

    raw_body = request.body
    content_enc = request.META.get('HTTP_CONTENT_ENCODING')

    if content_enc == 'gzip':
        raw_body = zlib.decompress(raw_body)

    return json.loads(raw_body.decode('utf-8'))


def normalize_feed_url(url):
    """
    Converts any URL to http:// or ftp:// so that it can be
    used with "wget". If the URL cannot be converted (invalid
    or unknown scheme), "None" is returned.

    This will also normalize feed:// and itpc:// to http://.

    >>> normalize_feed_url('itpc://example.org/podcast.rss')
    'http://example.org/podcast.rss'

    If no URL scheme is defined (e.g. "curry.com"), we will
    simply assume the user intends to add a http:// feed.

    >>> normalize_feed_url('curry.com')
    'http://curry.com/'

    There are even some more shortcuts for advanced users
    and lazy typists (see the source for details).

    >>> normalize_feed_url('fb:43FPodcast')
    'http://feeds.feedburner.com/43FPodcast'

    It will also take care of converting the domain name to
    all-lowercase (because domains are not case sensitive):

    >>> normalize_feed_url('http://Example.COM/')
    'http://example.com/'

    Some other minimalistic changes are also taken care of,
    e.g. a ? with an empty query is removed:

    >>> normalize_feed_url('http://example.org/test?')
    'http://example.org/test'

    Leading and trailing whitespace is removed

    >>> normalize_feed_url(' http://example.com/podcast.rss ')
    'http://example.com/podcast.rss'

    HTTP Authentication is removed to protect users' privacy

    >>> normalize_feed_url('http://a@b:c@host.com/')
    'http://host.com/'
    >>> normalize_feed_url('ftp://a:b:c@host.com/')
    'ftp://host.com/'
    >>> normalize_feed_url('http://i%2Fo:P%40ss%3A@host.com/')
    'http://host.com/'
    >>> normalize_feed_url('ftp://%C3%B6sterreich@host.com/')
    'ftp://host.com/'
    >>> normalize_feed_url('http://w%20x:y%20z@example.org/')
    'http://example.org/'
    >>> normalize_feed_url('http://example.com/x@y:z@test.com/')
    'http://example.com/x%40y%3Az%40test.com/'
    >>> normalize_feed_url('http://en.wikipedia.org/wiki/Ä')
    'http://en.wikipedia.org/wiki/%C3%84'
    >>> normalize_feed_url('http://en.wikipedia.org/w/index.php?title=Ä&action=edit')
    'http://en.wikipedia.org/w/index.php?title=%C3%84&action=edit'
    """
    url = url.strip()
    if not url or len(url) < 8:
        return None

    # This is a list of prefixes that you can use to minimize the amount of
    # keystrokes that you have to use.
    # Feel free to suggest other useful prefixes, and I'll add them here.
    PREFIXES = {
            'fb:': 'http://feeds.feedburner.com/%s',
            'yt:': 'http://www.youtube.com/rss/user/%s/videos.rss',
            'sc:': 'http://soundcloud.com/%s',
            'fm4od:': 'http://onapp1.orf.at/webcam/fm4/fod/%s.xspf',
            # YouTube playlists. To get a list of playlists per-user, use:
            # https://gdata.youtube.com/feeds/api/users/<username>/playlists
            'ytpl:': 'http://gdata.youtube.com/feeds/api/playlists/%s',
    }

    for prefix, expansion in PREFIXES.items():
        if url.startswith(prefix):
            url = expansion % (url[len(prefix):],)
            break

    # Assume HTTP for URLs without scheme
    if not '://' in url:
        url = 'http://' + url

    scheme, netloc, path, query, fragment = urllib.parse.urlsplit(url)

    # Schemes and domain names are case insensitive
    scheme, netloc = scheme.lower(), netloc.lower()

    # encode non-encoded characters
    path = urllib.parse.quote(path, '/%')
    query = urllib.parse.quote_plus(query, ':&=')

    # Remove authentication to protect users' privacy
    netloc = netloc.rsplit('@', 1)[-1]

    # Normalize empty paths to "/"
    if path == '':
        path = '/'

    # feed://, itpc:// and itms:// are really http://
    if scheme in ('feed', 'itpc', 'itms'):
        scheme = 'http'

    if scheme not in ('http', 'https', 'ftp', 'file'):
        return None

    # urlunsplit might return "a slighty different, but equivalent URL"
    return urllib.parse.urlunsplit((scheme, netloc, path, query, fragment))


def partition(items, predicate=bool):
    a, b = itertools.tee((predicate(item), item) for item in items)
    return ((item for pred, item in a if not pred),
            (item for pred, item in b if pred))


def split_quoted(s):
    """ Splits a quoted string

    >>> split_quoted('some "quoted text"') == ['some', 'quoted text']
    True

    >>> split_quoted('"quoted text') == ['quoted', 'text']
    True

    # 4 quotes here are 2 in the doctest is one in the actual string
    >>> split_quoted('text\\\\') == ['text']
    True
    """

    try:
        # split by whitespace, preserve quoted substrings
        keywords = shlex.split(s)

    except ValueError:
        # No closing quotation (eg '"text')
        # No escaped character (eg '\')
        s = s.replace('"', '').replace("'", '').replace('\\', '')
        keywords = shlex.split(s)

    return keywords


def edit_link(obj):
    """ Return the link to the Django Admin Edit page """
    return reverse('admin:%s_%s_change' % (obj._meta.app_label,
                                           obj._meta.model_name),
                   args=(obj.pk,))


def random_token(length=32):
    import random
    import string
    return "".join(random.sample(string.ascii_letters+string.digits, length))


def to_maxlength(cls, field, val):
    """ Cut val to the maximum length of cls's field """
    if val is None:
        return None

    max_length = cls._meta.get_field(field).max_length
    orig_length = len(val)
    if orig_length > max_length:
        val = val[:max_length]
        logger.warn('%s.%s length reduced from %d to %d',
                    cls.__name__, field, orig_length, max_length)

    return val


def get_domain(url):
    """ Returns the domain name of a URL

    >>> get_domain('http://example.com')
    'example.com'

    >>> get_domain('https://example.com:80/my-podcast/feed.rss')
    'example.com'
    """
    netloc = urllib.parse.urlparse(url).netloc
    try:
        port_idx = netloc.index(':')
        return netloc[:port_idx]

    except ValueError:
        return netloc


def set_ordered_entries(obj, new_entries, existing, EntryClass,
                        value_name, parent_name):
    """ Update the object's entries to the given list

    'new_entries' should be a list of objects that are later wrapped in
    EntryClass instances. 'value_name' is the name of the EntryClass property
    that contains the values; 'parent_name' is the one that references obj.

    Entries that do not exist are created. Existing entries that are not in
    'new_entries' are deleted. """

    logger.info('%d existing entries', len(existing))

    logger.info('%d new entries', len(new_entries))

    with transaction.atomic():
        max_order = max([s.order for s in existing.values()] +
                        [len(new_entries)])
        logger.info('Renumbering entries starting from %d', max_order+1)
        for n, entry in enumerate(existing.values(), max_order+1):
            entry.order = n
            entry.save()

    logger.info('%d existing entries', len(existing))

    for n, entry in enumerate(new_entries):
        try:
            e = existing.pop(entry)
            logger.info('Updating existing entry %d: %s', n, entry)
            e.order = n
            e.save()
        except KeyError:
            logger.info('Creating new entry %d: %s', n, entry)
            try:
                links = {
                    value_name: entry,
                    parent_name: obj,
                }
                from mygpo.podcasts.models import ScopedModel
                if issubclass(EntryClass, ScopedModel):
                    links['scope'] = obj.scope

                EntryClass.objects.create(order=n, **links)
            except IntegrityError as ie:
                logger.warn('Could not create enry for %s: %s', obj, ie)

    with transaction.atomic():
        delete = [s.pk for s in existing.values()]
        logger.info('Deleting %d entries', len(delete))
        EntryClass.objects.filter(id__in=delete).delete()
